import os
from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

VECTOR_DB_URL = os.getenv("VECTOR_DB_URL")
SUPPLIER_DOC_COLLECTION = os.getenv("SUPPLIER_DOC_COLLECTION")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

# MongoDB client
mongo_client = AsyncIOMotorClient(MONGO_URL)
database = mongo_client["supply_chain_analyzer"]

# Collections
suppliers_collection = database["suppliers"]
document_logs_collection = database["document_logs"]

# Vector DB client (assuming Qdrant)
qdrant = QdrantClient(url=VECTOR_DB_URL)
