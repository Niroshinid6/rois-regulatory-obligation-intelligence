from typing import List, Any
from pydantic import BaseModel

class DashboardMetricsResponse(BaseModel):
    total_documents: int
    processed_documents: int
    total_obligations: int
    pending_reviews: int
    approved_obligations: int
    new_obligations: int
    modified_obligations: int
    retired_obligations: int
    impacted_controls_count: int
    recent_documents: List[Any] = []
    recent_obligations: List[Any] = []
    recent_changes: List[Any] = []
    pending_review_items: List[Any] = []
