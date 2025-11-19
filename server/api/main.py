import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

# Load environment variables
load_dotenv()

# File upload settings
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Import modules
from server.api.routes.suppliers import router as suppliers_router
from server.api.routes.rag import router as rag_router
from server.connections import qdrant, mongo_client, database  # Initialize connections

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

# Include routers
app.include_router(suppliers_router)
app.include_router(rag_router)
