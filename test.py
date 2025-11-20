from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="supplier_docs",
    vectors_config=VectorParams(
        size=384,            # embedding size for all-MiniLM-L6-v2
        distance=Distance.COSINE
    )
)

print("Collection created!")