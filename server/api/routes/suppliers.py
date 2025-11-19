import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from datetime import datetime
from server.connections import suppliers_collection, document_logs_collection, qdrant, SUPPLIER_DOC_COLLECTION
from server.models.models import SupplierCreate
import mammoth

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/suppliers")
async def list_suppliers():
    """Fetch all supplier names from database for risk analysis selection."""
    try:
        # Get all supplier names from MongoDB for analysis selection
        suppliers_cursor = suppliers_collection.find({"active": True}, {"name": 1, "id": 1})
        suppliers = await suppliers_cursor.to_list(length=None)

        # Return supplier names
        supplier_names = [supplier["name"] for supplier in suppliers]

        return {"suppliers": sorted(supplier_names)}

    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve supplier list: {e}")


@router.get("/api/suppliers")
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


@router.post("/api/suppliers")
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
            "active": new_supplier["active"],
            "document_count": new_supplier["document_count"],
            "last_assessment": new_supplier["last_assessment"],
            "created_at": new_supplier["created_at"]
        }

        return {"supplier": response_supplier}
    except Exception as e:
        raise HTTPException(500, f"Failed to create supplier: {e}")


@router.put("/api/suppliers/{supplier_id}")
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
            "active": updated_supplier.get("active", True),
            "document_count": updated_supplier.get("document_count", 0),
            "last_assessment": updated_supplier["last_assessment"],
            "created_at": updated_supplier["created_at"]
        }

        return {"supplier": response_supplier}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to update supplier: {e}")


@router.delete("/api/suppliers/{supplier_id}")
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


@router.post("/api/suppliers/{supplier_id}/documents")
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


@router.get("/api/suppliers/{supplier_id}/documents")
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


@router.get("/api/documents/{document_id}/preview")
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
