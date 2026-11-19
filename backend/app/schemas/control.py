from typing import Optional, List
from pydantic import BaseModel

class ControlCategoryResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class ObligationControlResponse(BaseModel):
    id: int
    obligation_id: int
    control_category_id: int
    category_code: str
    category_name: str
    rationale: str
    mapping_method: str
    review_status: str
    obligation_code: Optional[str] = None
    obligation_text: Optional[str] = None

    class Config:
        from_attributes = True

class MappingReviewRequest(BaseModel):
    review_status: str  # approved, rejected
    rationale: Optional[str] = None
