import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchRequest
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()
MODEL_PROVIDER_KEY = os.getenv("MODEL_PROVIDER_KEY")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL")
SUPPLIER_DOC_COLLECTION = os.getenv("SUPPLIER_DOC_COLLECTION")

if not MODEL_PROVIDER_KEY:
    raise ValueError("MODEL_PROVIDER_KEY is missing in .env")

# ==========================
# CONFIGURATION
# ==========================

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM = "meta-llama/llama-3.3-70b-instruct"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

RISK_TEMPLATE = """
You are a domain expert specialized in supply chain risk analysis.

### Response Instructions:
- Assess the risk level as Low, Moderate, or High.
- Provide a summary justification.
- Include specific extracted evidence.

### Reference Context:
{context}

### User Query:
{query}
"""

# ==========================
# INITIALIZATION
# ==========================

app = FastAPI(title="AI Supply Chain Risk Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Embeddings
embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

# Vector DB client (assuming Qdrant for now)
qdrant = QdrantClient(url=VECTOR_DB_URL)


# ==========================
# REQUEST MODELS
# ==========================

class AnalyzeQuery(BaseModel):
    query: str
    vendor_ids: List[str]


# ==========================
# ROUTES
# ==========================

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/suppliers")
def list_suppliers():
    """Fetch distinct vendor IDs stored as payload metadata."""
    try:
        scroll = qdrant.scroll(
            collection_name=SUPPLIER_DOC_COLLECTION,
            limit=200,
            with_payload=True
        )

        vendors = set()
        for point in scroll[0]:
            vid = point.payload.get("vendor_id")
            if vid:
                vendors.add(vid)

        return {"suppliers": sorted(list(vendors))}

    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve supplier list: {e}")


# ==========================
# MAIN RAG LOGIC
# ==========================

@app.post("/analyze")
def analyze_risk(data: AnalyzeQuery):
    user_query = data.query.strip()
    vendor_ids = data.vendor_ids

    if not user_query:
        raise HTTPException(400, "Query cannot be empty.")

    # SSR Step 1: Generate Hypothetical Analysis Paragraph
    ssr_prompt = f"""
    You are an expert in supply chain risk analysis.
    Generate a hypothetical but realistic analytical snippet that represents what an answer to the following risk query might look like.
    The snippet should be a short paragraph addressing the query.

    Query: {user_query}

    Hypothetical Analysis:
    """
    try:
        ssr_response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {MODEL_PROVIDER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM,
                "messages": [
                    {"role": "user", "content": ssr_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 200
            }
        ).json()
        hypothetical_analysis = ssr_response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise HTTPException(500, f"SSR generation error: {e}")

    # SSR Step 2: Embed the Hypothetical Analysis
    ssr_embedding = embedder.embed_query(hypothetical_analysis)

    # SSR Step 3: Build filter for selected vendors
    vendor_filter = None
    if vendor_ids:
        vendor_filter = Filter(
            must=[
                FieldCondition(
                    key="vendor_id",
                    match=MatchValue(value=vid)
                ) for vid in vendor_ids
            ]
        )

    # SSR Step 4: Perform vector search using SSR embedding (top 8 chunks)
    try:
        search_result = qdrant.search(
            collection_name=SUPPLIER_DOC_COLLECTION,
            query_vector=ssr_embedding,
            limit=8,
            query_filter=vendor_filter
        )
    except Exception as e:
        raise HTTPException(500, f"Vector DB search error: {e}")

    if not search_result:
        return {"risk_level": "Low", "evidence": [], "summary": "No relevant material found."}

    # SSR Step 5: Aggregate content and pick top chunks
    scored_chunks = []
    for hit in search_result:
        score = float(hit.score)
        payload = hit.payload
        text = payload.get("text", "")

        # Threshold to avoid weak matches
        if score < 0.10:
            continue

        scored_chunks.append((text, payload.get("source", "Unknown")))

    if not scored_chunks:
        return {"risk_level": "Low", "evidence": [], "summary": "No sufficiently relevant content found."}

    # Keep only first 3 best matches
    context_blocks = [chunk for chunk, src in scored_chunks[:3]]

    # SSR Step 6: Compose final context
    full_context = "\n\n---\n\n".join(context_blocks)

    # SSR Step 7: Build prompt for LLM using Query + Context + Hypothetical Analysis
    prompt = f"""
    You are a domain expert specialized in supply chain risk analysis.

    ### Response Instructions:
    - Assess the risk level as Low, Moderate, or High.
    - Provide a summary justification.
    - Include specific extracted evidence.

    ### Reference Context:
    {full_context}

    ### Hypothetical Analysis (for reference):
    {hypothetical_analysis}

    ### User Query:
    {user_query}
    """

    # SSR Step 8: Call LLM for final risk assessment
    try:
        llm_output = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {MODEL_PROVIDER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM,
                "messages": [
                    {"role": "system", "content": "Provide risk assessment with level, summary, and evidence."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0
            }
        ).json()

        assessment_text = llm_output["choices"][0]["message"]["content"].strip()

    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")

    # SSR Step 9: Parse the assessment (simplified parsing)
    # Assume the response starts with "Risk Level: High" etc.
    risk_level = "Moderate"  # default
    if "High" in assessment_text[:50]:
        risk_level = "High"
    elif "Low" in assessment_text[:50]:
        risk_level = "Low"

    summary = assessment_text  # For simplicity, use the whole text as summary

    # Extract evidence as document names
    evidence = sorted(list({
        src
        for _, src in scored_chunks[:3]
    }))

    return {
        "risk_level": risk_level,
        "evidence": evidence,
        "summary": summary
    }
