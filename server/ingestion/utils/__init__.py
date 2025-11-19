import os
import requests
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM = "meta-llama/llama-3.1-8b-instruct:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("MODEL_PROVIDER_KEY")


# Check if API key is set and valid
if not OPENROUTER_API_KEY:
    raise ValueError(
        "MODEL_PROVIDER_KEY is not set properly in .env file.\n"
        "Please get an API key from https://openrouter.ai/keys and update MODEL_PROVIDER_KEY in your .env file."
    )

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
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": LLM,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        r = requests.post(OPENROUTER_URL, json=payload, headers=headers)
        resp = r.json()

        # ---- Case 1: OpenAI-style response ----
        if "choices" in resp and resp["choices"]:
            choice = resp["choices"][0]

            # Format A: choices[].message.content
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]

            # Format B: choices[].text  (Anthropic / Cohere models)
            if "text" in choice:
                return choice["text"]

            # Format C: multi-part content
            if "content" in choice:
                parts = choice["content"]
                if isinstance(parts, list):
                    return "".join([p.get("text", "") for p in parts])
                if isinstance(parts, str):
                    return parts

        # ---- Case 2: OpenRouter error object ----
        if "error" in resp:
            raise Exception(resp["error"])

        raise Exception("Unknown LLM response format")

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
