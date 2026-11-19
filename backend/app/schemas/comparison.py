from typing import Optional, List, Any
from pydantic import BaseModel
from app.schemas.obligation import ObligationResponse

class ComparisonCreate(BaseModel):
    title: Optional[str] = None
    base_document_id: int
    target_document_id: int

class ObligationChangeResponse(BaseModel):
    id: int
    comparison_id: int
    previous_obligation_id: Optional[int] = None
    current_obligation_id: Optional[int] = None
    change_type: str  # new, modified, retired, unchanged, requires_review
    change_explanation: str
    diff_details: Any
    human_verified: bool
    previous_obligation: Optional[ObligationResponse] = None
    current_obligation: Optional[ObligationResponse] = None

    class Config:
        from_attributes = True

class ComparisonResponse(BaseModel):
    id: int
    title: str
    base_document_id: int
    target_document_id: int
    base_document_title: Optional[str] = None
    base_circular_number: Optional[str] = None
    target_document_title: Optional[str] = None
    target_circular_number: Optional[str] = None
    status: str
    created_at: str
    changes: List[ObligationChangeResponse] = []

    class Config:
        from_attributes = True
