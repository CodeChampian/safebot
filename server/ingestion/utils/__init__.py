import os
import uuid
import requests
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

# Load environment variables
load_dotenv()

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM = "openai/gpt-oss-20b:free"
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


def extract_text_from_file(file_path):
    """Extract text content from various file formats."""
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install it with: pip install PyPDF2")
        except Exception as e:
            raise Exception(f"Error processing PDF: {e}")

    elif file_extension == '.docx':
        try:
            import mammoth
            with open(file_path, 'rb') as file:
                result = mammoth.extract_raw_text(file)
                return result.value
        except Exception as e:
            raise Exception(f"Error processing DOCX: {e}")

    elif file_extension == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error processing TXT: {e}")

    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def chunk_and_embed_document(file_path, document_id, vendor_id, filename, qdrant_client, collection_name):
    """Chunk document and store embeddings in Qdrant."""
    try:
        # Extract text from the file
        raw_text = extract_text_from_file(file_path)

        if not raw_text.strip():
            return [], "No text content extracted from document"

        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # 1000 characters per chunk
            chunk_overlap=200,  # 200 characters overlap
            length_function=len,
            separators=["\n\n", "\n", " ", ""]  # Try to split on paragraphs, then lines, then spaces
        )

        # Split the text into chunks
        chunks = text_splitter.split_text(raw_text)

        # Prepare points for Qdrant
        points = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Only process non-empty chunks
                # Create embedding for the chunk
                embedding = embedder.embed_query(chunk)

                # Create point for Qdrant
                chunk_id = str(uuid.uuid4())
                point = PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "document_id": document_id,
                        "vendor_id": vendor_id,
                        "filename": filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "source": filename
                    }
                )
                points.append(point)

        # Upsert points to Qdrant
        if points:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )

        return points, f"Successfully processed {len(points)} chunks"

    except Exception as e:
        raise Exception(f"Error processing document: {e}")


def delete_document_chunks(qdrant_client, collection_name, document_id):
    """Delete all chunks for a specific document from Qdrant."""
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Create filter to find all chunks for this document
        document_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )

        # Delete all points matching the filter
        qdrant_client.delete(
            collection_name=collection_name,
            points_selector=document_filter
        )

        return True, "Document chunks deleted successfully"

    except Exception as e:
        raise Exception(f"Error deleting document chunks: {e}")
