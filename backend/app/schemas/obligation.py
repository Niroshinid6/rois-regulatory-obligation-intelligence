from typing import Optional, List, Any
from pydantic import BaseModel

class EvidenceSpanResponse(BaseModel):
    id: int
    page_number: int
    exact_text: str
    char_start: int
    char_end: int
    bounding_box: Any
    confidence: float

    class Config:
        from_attributes = True

class ObligationResponse(BaseModel):
    id: int
    obligation_code: str
    document_id: int
    source_page: int
    obligation_text: str
    responsible_entity: Optional[str] = None
    required_action: str
    deadline: Optional[str] = None
    conditions: List[str] = []
    exceptions: List[str] = []
    confidence_score: float
    evidence_status: str
    review_status: str
    extraction_method: str
    created_at: str
    document_title: Optional[str] = None
    circular_number: Optional[str] = None
    evidence_span: Optional[EvidenceSpanResponse] = None

    class Config:
        from_attributes = True

class ObligationReviewRequest(BaseModel):
    action: str  # approved, rejected, corrected
    responsible_entity: Optional[str] = None
    required_action: Optional[str] = None
    deadline: Optional[str] = None
    comments: Optional[str] = None

class ObligationListResponse(BaseModel):
    total: int
    items: List[ObligationResponse]
