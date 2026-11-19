from typing import Optional, List, Any
from pydantic import BaseModel

class ImpactReportCreate(BaseModel):
    document_id: Optional[int] = None
    comparison_id: Optional[int] = None
    title: Optional[str] = None

class ImpactReportResponse(BaseModel):
    id: int
    title: str
    document_id: Optional[int] = None
    comparison_id: Optional[int] = None
    executive_summary: str
    metrics: Any
    report_data: Any
    created_at: str
    generated_by: Optional[int] = None

    class Config:
        from_attributes = True
