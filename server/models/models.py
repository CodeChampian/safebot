from pydantic import BaseModel
from typing import List, Optional


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
