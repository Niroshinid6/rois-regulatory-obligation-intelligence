from typing import Optional, Any
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Any
    ip_address: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
