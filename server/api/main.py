import os
import requests
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchRequest, PointStruct
from langchain_huggingface import HuggingFaceEmbeddings
import mammoth

# Load environment variables
load_dotenv()
MODEL_PROVIDER_KEY = os.getenv("MODEL_PROVIDER_KEY")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL")
SUPPLIER_DOC_COLLECTION = os.getenv("SUPPLIER_DOC_COLLECTION")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

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

# Mount static files directory for file serving
# Add custom CORS headers for file serving
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

class CORSMiddlewareForFiles(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/files/"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(CORSMiddlewareForFiles)
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

# Embeddings
embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

# Vector DB client (assuming Qdrant for now)
qdrant = QdrantClient(url=VECTOR_DB_URL)

# MongoDB client
mongo_client = AsyncIOMotorClient(MONGO_URL)
database = mongo_client["supply_chain_analyzer"]

# Collections
suppliers_collection = database["suppliers"]
document_logs_collection = database["document_logs"]


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
    active: bool = True

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
async def get_all_suppliers():
    """Get all suppliers."""
    try:
        suppliers_cursor = suppliers_collection.find()
        suppliers = await suppliers_cursor.to_list(length=None)
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
                "active": supplier.get("active", True),
                "document_count": supplier.get("document_count", 0),
                "last_assessment": supplier["last_assessment"],
                "created_at": supplier["created_at"]
            })
        return {"suppliers": formatted_suppliers}
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve suppliers: {e}")


@app.post("/api/suppliers")
async def create_supplier(supplier_data: SupplierCreate):
    """Create a new supplier."""
    try:
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
            "active": supplier_data.active,
            "created_at": datetime.now().isoformat(),
            "last_assessment": datetime.now().isoformat(),
            "document_count": 0
        }

        await suppliers_collection.insert_one(new_supplier)

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
            "last_assessment": new_supplier["last_assessment"],
            "created_at": new_supplier["created_at"]
        }

        return {"supplier": response_supplier}
    except Exception as e:
        raise HTTPException(500, f"Failed to create supplier: {e}")


@app.put("/api/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, supplier_data: SupplierCreate):
    """Update an existing supplier."""
    try:
        supplier = await suppliers_collection.find_one({"id": supplier_id})
        if not supplier:
            raise HTTPException(404, "Supplier not found")

        # Update supplier data
        update_data = {
            "name": supplier_data.name,
            "category": supplier_data.category,
            "location": supplier_data.location,
            "contact_email": supplier_data.contact_email,
            "contact_phone": supplier_data.contact_phone,
            "description": supplier_data.description,
            "active": supplier_data.active,
            "last_assessment": datetime.now().isoformat()
        }

        await suppliers_collection.update_one({"id": supplier_id}, {"$set": update_data})

        # Return updated supplier
        updated_supplier = await suppliers_collection.find_one({"id": supplier_id})
        response_supplier = {
            "id": updated_supplier["id"],
            "name": updated_supplier["name"],
            "category": updated_supplier["category"],
            "location": updated_supplier["location"],
            "riskLevel": updated_supplier["risk_level"],
            "contact_email": updated_supplier.get("contact_email"),
            "contact_phone": updated_supplier.get("contact_phone"),
            "description": updated_supplier.get("description"),
            "document_count": updated_supplier.get("document_count", 0),
            "last_assessment": updated_supplier["last_assessment"],
            "created_at": updated_supplier["created_at"]
        }

        return {"supplier": response_supplier}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to update supplier: {e}")


@app.delete("/api/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    """Delete a supplier."""
    try:
        supplier = await suppliers_collection.find_one({"id": supplier_id})
        if not supplier:
            raise HTTPException(404, "Supplier not found")

        await suppliers_collection.delete_one({"id": supplier_id})
        return {"message": "Supplier deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete supplier: {e}")


@app.post("/api/suppliers/{supplier_id}/documents")
async def upload_supplier_document(supplier_id: str, file: UploadFile = File(...)):
    """Upload a document for a specific supplier."""
    try:
        supplier = await suppliers_collection.find_one({"id": supplier_id})
        if not supplier:
            raise HTTPException(404, "Supplier not found")

        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg']
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(400, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")

        # Generate unique file name
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}{file_extension}"

        # Create supplier's document directory
        supplier_dir = os.path.join(UPLOAD_DIR, supplier_id)
        if not os.path.exists(supplier_dir):
            os.makedirs(supplier_dir)

        # Save the file
        file_path = os.path.join(supplier_dir, file_name)
        try:
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
        except Exception as e:
            raise HTTPException(500, f"Failed to save file: {e}")

        # Log document upload
        document_log = {
            "supplier_id": supplier_id,
            "file_id": file_id,
            "filename": file.filename,
            "stored_filename": file_name,
            "file_path": file_path,
            "file_size": len(content),
            "file_extension": file_extension,
            "uploaded_at": datetime.now().isoformat()
        }
        await document_logs_collection.insert_one(document_log)

        # Update document count for supplier
        await suppliers_collection.update_one(
            {"id": supplier_id},
            {"$inc": {"document_count": 1}}
        )

        return {"message": "Document uploaded successfully", "file_path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to upload document: {e}")


@app.get("/api/suppliers/{supplier_id}/documents")
async def get_supplier_documents(supplier_id: str):
    """Get all documents for a specific supplier."""
    try:
        supplier = await suppliers_collection.find_one({"id": supplier_id})
        if not supplier:
            raise HTTPException(404, "Supplier not found")

        # Fetch document logs from MongoDB
        documents_cursor = document_logs_collection.find({"supplier_id": supplier_id}).sort("uploaded_at", -1)
        documents = await documents_cursor.to_list(length=None)

        # Format for response
        formatted_documents = []
        for doc in documents:
            # Create URL for frontend access (files served at /files endpoint)
            relative_path = doc["file_path"].replace(UPLOAD_DIR, "").lstrip(os.sep).replace("\\", "/")
            file_url = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/files/{relative_path}"

            formatted_documents.append({
                "id": doc["file_id"],
                "filename": doc["filename"],
                "file_path": doc["file_path"],
                "url": file_url,
                "size": doc["file_size"],
                "uploaded_at": doc["uploaded_at"],
                "extension": doc["file_extension"]
            })

        return {"documents": formatted_documents}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve documents: {e}")


@app.get("/api/documents/{document_id}/preview")
async def preview_document(document_id: str):
    """Convert a DOCX document to HTML for preview."""
    try:
        # Find the document in the database
        document = await document_logs_collection.find_one({"file_id": document_id})
        if not document:
            raise HTTPException(404, "Document not found")

        file_path = document["file_path"]

        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(404, "Document file not found")

        # Get file extension
        file_extension = document.get("file_extension", "").lower()

        # Only process DOCX files for now
        if file_extension not in [".docx"]:
            raise HTTPException(400, "Unsupported file type for preview")

        # Convert DOCX to HTML using mammoth
        with open(file_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)

            # Get the HTML content
            html_content = result.value

            # Create a styled HTML page
            full_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{document["filename"]} - Preview</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .document-container {{
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .document-header {{
                        text-align: center;
                        margin-bottom: 30px;
                        padding-bottom: 20px;
                        border-bottom: 1px solid #eee;
                    }}
                    .document-header h1 {{
                        color: #333;
                        margin-bottom: 10px;
                        font-size: 24px;
                    }}
                    .document-meta {{
                        color: #666;
                        font-size: 14px;
                    }}
                    .document-content {{
                        color: #333;
                        overflow-wrap: break-word;
                    }}
                    .document-content h1,
                    .document-content h2,
                    .document-content h3,
                    .document-content h4,
                    .document-content h5,
                    .document-content h6 {{
                        color: #2c3e50;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }}
                    .document-content p {{
                        margin-bottom: 1em;
                    }}
                    .document-content ul,
                    .document-content ol {{
                        margin-bottom: 1em;
                        padding-left: 30px;
                    }}
                    .document-content table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin-bottom: 1em;
                    }}
                    .document-content td,
                    .document-content th {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    .document-content th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="document-container">
                    <div class="document-header">
                        <h1>{document["filename"]}</h1>
                        <div class="document-meta">
                            Uploaded: {document["uploaded_at"]}
                        </div>
                    </div>
                    <div class="document-content">
                        {html_content}
                    </div>
                </div>
            </body>
            </html>
            """

            return HTMLResponse(content=full_html, status_code=200)

    except HTTPException:
        raise
    except mammoth.DocumentConverterError as e:
        raise HTTPException(422, f"Document conversion error: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Failed to preview document: {str(e)}")


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
