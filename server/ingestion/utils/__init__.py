import os
import requests
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM = "meta-llama/llama-3.3-70b-instruct"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_PROVIDER_KEY = os.getenv("MODEL_PROVIDER_KEY")

# Uncomment for production
# if not MODEL_PROVIDER_KEY:
#     raise ValueError("MODEL_PROVIDER_KEY is missing in .env")

# Embeddings
embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

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


def generate_ssr_prompt(user_query):
    """Generate hypothetical analysis for SSR."""
    ssr_prompt = f"""
    You are an expert in supply chain risk analysis.
    Generate a hypothetical but realistic analytical snippet that represents what an answer to the following risk query might look like.
    The snippet should be a short paragraph addressing the query.

    Query: {user_query}

    Hypothetical Analysis:
    """
    return ssr_prompt


def call_llm(messages, temperature=0.7, max_tokens=200):
    """Call LLM with given messages."""
    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {MODEL_PROVIDER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        ).json()
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise Exception(f"LLM call error: {e}")


def parse_risk_assessment(assessment_text):
    """Parse risk assessment to extract risk level."""
    risk_level = "Moderate"  # default
    if "High" in assessment_text[:50]:
        risk_level = "High"
    elif "Low" in assessment_text[:50]:
        risk_level = "Low"
    return risk_level
