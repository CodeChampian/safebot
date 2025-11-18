import os
import requests
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional
from datetime import datetime
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchRequest, PointStruct
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()
MODEL_PROVIDER_KEY = os.getenv("MODEL_PROVIDER_KEY")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL")
SUPPLIER_DOC_COLLECTION = os.getenv("SUPPLIER_DOC_COLLECTION")

# File upload settings
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Uncomment for production
# if not MODEL_PROVIDER_KEY:
#     raise ValueError("MODEL_PROVIDER_KEY is missing in .env")

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

# In-memory supplier storage (in production, use a proper database)
suppliers_db = {}

# Initialize with sample suppliers
def initialize_sample_suppliers():
    now = datetime.now().isoformat()
    sample_suppliers = [
        {
            "id": "SUP-001",
            "name": "TechSolutions Inc.",
            "category": "Technology",
            "location": "USA",
            "risk_level": "Low",
            "contact_email": "contact@techsolutions.com",
            "contact_phone": "+1-555-0101",
            "description": "Leading provider of enterprise software solutions",
            "created_at": now,
            "last_assessment": now,
            "document_count": 3
        },
        {
            "id": "SUP-002",
            "name": "Global Manufacturing Ltd.",
            "category": "Manufacturing",
            "location": "China",
            "risk_level": "Moderate",
            "contact_email": "info@globalmfg.com",
            "contact_phone": "+86-21-1234-5678",
            "description": "Specialized in industrial component manufacturing",
            "created_at": now,
            "last_assessment": now,
            "document_count": 2
        },
        {
            "id": "SUP-003",
            "name": "Logistics Pro GmbH",
            "category": "Logistics",
            "location": "Germany",
            "risk_level": "Low",
            "contact_email": "support@logisticspro.de",
            "contact_phone": "+49-30-9876-5432",
            "description": "International shipping and logistics services",
            "created_at": now,
            "last_assessment": now,
            "document_count": 4
        },
        {
            "id": "SUP-004",
            "name": "SupplyChain Services Inc.",
            "category": "Services",
            "location": "India",
            "risk_level": "High",
            "contact_email": "admin@supplychainservices.in",
            "contact_phone": "+91-22-3456-7890",
            "description": "Comprehensive supply chain management consulting",
            "created_at": now,
            "last_assessment": now,
            "document_count": 1
        },
        {
            "id": "SUP-005",
            "name": "Premier Materials Co.",
            "category": "Manufacturing",
            "location": "Japan",
            "risk_level": "Low",
            "contact_email": "sales@premiermaterials.co.jp",
            "contact_phone": "+81-3-1234-5678",
            "description": "High-quality raw materials and components",
            "created_at": now,
            "last_assessment": now,
            "document_count": 5
        }
    ]
    for supplier in sample_suppliers:
        suppliers_db[supplier["id"]] = supplier

# Initialize sample data
initialize_sample_suppliers()


# ==========================
# REQUEST MODELS
# ==========================

class AnalyzeQuery(BaseModel):
    query: str
    vendor_ids: List[str]

class SupplierCreate(BaseModel):
    name: str
    category: str
    location: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None

class Supplier(BaseModel):
    id: str
    name: str
    category: str
    location: str
    risk_level: str = "Low"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    created_at: str
    last_assessment: str
    document_count: int = 0


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
# SUPPLIER MANAGEMENT ROUTES
# ==========================

@app.get("/api/suppliers")
def get_all_suppliers():
    """Get all suppliers."""
    suppliers = list(suppliers_db.values())
    # Format data to match frontend expectations
    formatted_suppliers = []
    for supplier in suppliers:
        formatted_suppliers.append({
            "id": supplier["id"],
            "name": supplier["name"],
            "category": supplier["category"],
            "location": supplier["location"],
            "riskLevel": supplier["risk_level"],
            "contact_email": supplier.get("contact_email"),
            "contact_phone": supplier.get("contact_phone"),
            "description": supplier.get("description"),
            "document_count": supplier.get("document_count", 0),
            "last_assessment": supplier["last_assessment"],
            "created_at": supplier["created_at"]
        })
    return {"suppliers": formatted_suppliers}


@app.post("/api/suppliers")
def create_supplier(supplier_data: SupplierCreate):
    """Create a new supplier."""
    # Generate unique ID
    supplier_id = f"SUP-{str(uuid.uuid4())[:8].upper()}"

    new_supplier = {
        "id": supplier_id,
        "name": supplier_data.name,
        "category": supplier_data.category,
        "location": supplier_data.location,
        "risk_level": "Low",  # Default risk level
        "contact_email": supplier_data.contact_email,
        "contact_phone": supplier_data.contact_phone,
        "description": supplier_data.description,
        "created_at": datetime.now().isoformat(),
        "last_assessment": datetime.now().isoformat(),
        "document_count": 0
    }

    suppliers_db[supplier_id] = new_supplier

    # Return formatted response matching frontend expectations
    response_supplier = {
        "id": new_supplier["id"],
        "name": new_supplier["name"],
        "category": new_supplier["category"],
        "location": new_supplier["location"],
        "riskLevel": new_supplier["risk_level"],
        "contact_email": new_supplier["contact_email"],
        "contact_phone": new_supplier["contact_phone"],
        "description": new_supplier["description"],
        "document_count": new_supplier["document_count"],
        "last_assessment": new_supplier["last_assessment"]
    }

    return {"supplier": response_supplier}


@app.put("/api/suppliers/{supplier_id}")
def update_supplier(supplier_id: str, supplier_data: SupplierCreate):
    """Update an existing supplier."""
    if supplier_id not in suppliers_db:
        raise HTTPException(404, "Supplier not found")

    # Update supplier data
    suppliers_db[supplier_id].update({
        "name": supplier_data.name,
        "category": supplier_data.category,
        "location": supplier_data.location,
        "contact_email": supplier_data.contact_email,
        "contact_phone": supplier_data.contact_phone,
        "description": supplier_data.description,
        "last_assessment": datetime.now().isoformat()
    })

    # Return updated supplier
    supplier = suppliers_db[supplier_id]
    response_supplier = {
        "id": supplier["id"],
        "name": supplier["name"],
        "category": supplier["category"],
        "location": supplier["location"],
        "riskLevel": supplier["risk_level"],
        "contact_email": supplier["contact_email"],
        "contact_phone": supplier["contact_phone"],
        "description": supplier["description"],
        "document_count": supplier["document_count"],
        "last_assessment": supplier["last_assessment"]
    }

    return {"supplier": response_supplier}


@app.delete("/api/suppliers/{supplier_id}")
def delete_supplier(supplier_id: str):
    """Delete a supplier."""
    if supplier_id not in suppliers_db:
        raise HTTPException(404, "Supplier not found")

    del suppliers_db[supplier_id]
    return {"message": "Supplier deleted successfully"}


@app.post("/api/suppliers/{supplier_id}/documents")
async def upload_supplier_document(supplier_id: str, file: UploadFile = File(...)):
    """Upload a document for a specific supplier."""
    if supplier_id not in suppliers_db:
        raise HTTPException(404, "Supplier not found")

    # Validate file type
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(400, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")

    # Create supplier's document directory
    supplier_dir = os.path.join(UPLOAD_DIR, supplier_id)
    if not os.path.exists(supplier_dir):
        os.makedirs(supplier_dir)

    # Save the file
    file_path = os.path.join(supplier_dir, f"{uuid.uuid4()}{file_extension}")
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {e}")

    # Update document count for supplier
    suppliers_db[supplier_id]["document_count"] += 1

    return {"message": "Document uploaded successfully", "file_path": file_path}


@app.get("/api/suppliers/{supplier_id}/documents")
def get_supplier_documents(supplier_id: str):
    """Get all documents for a specific supplier."""
    if supplier_id not in suppliers_db:
        raise HTTPException(404, "Supplier not found")

    supplier_dir = os.path.join(UPLOAD_DIR, supplier_id)
    if not os.path.exists(supplier_dir):
        return {"documents": []}

    documents = []
    for filename in os.listdir(supplier_dir):
        file_path = os.path.join(supplier_dir, filename)
        if os.path.isfile(file_path):
            # Get file info
            file_stat = os.stat(file_path)
            documents.append({
                "filename": filename,
                "file_path": file_path,
                "size": file_stat.st_size,
                "uploaded_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "extension": os.path.splitext(filename)[1]
            })

    return {"documents": documents}


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
