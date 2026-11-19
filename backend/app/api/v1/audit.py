import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit Ledger"])

@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "management", "compliance_officer"]))
):
    query = db.query(AuditLog)

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    if action:
        query = query.filter(AuditLog.action == action)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for log in logs:
        results.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_email=log.user.email if log.user else None,
            user_name=log.user.full_name if log.user else "System",
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=json.loads(log.details_json or "{}"),
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat()
        ))

    return results
