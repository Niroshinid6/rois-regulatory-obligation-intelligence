import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.obligation import Obligation
from app.models.document import EvidenceSpan
from app.models.review import ReviewRecord
from app.schemas.obligation import ObligationResponse, ObligationListResponse, ObligationReviewRequest, EvidenceSpanResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/obligations", tags=["Obligation Intelligence"])

def format_obligation_response(o: Obligation) -> ObligationResponse:
    span_resp = None
    if o.evidence_span:
        span_resp = EvidenceSpanResponse(
            id=o.evidence_span.id,
            page_number=o.evidence_span.page_number,
            exact_text=o.evidence_span.exact_text,
            char_start=o.evidence_span.char_start,
            char_end=o.evidence_span.char_end,
            bounding_box=json.loads(o.evidence_span.bounding_box_json or "{}"),
            confidence=o.evidence_span.confidence
        )

    return ObligationResponse(
        id=o.id,
        obligation_code=o.obligation_code,
        document_id=o.document_id,
        source_page=o.source_page,
        obligation_text=o.obligation_text,
        responsible_entity=o.responsible_entity,
        required_action=o.required_action,
        deadline=o.deadline,
        conditions=json.loads(o.conditions_json or "[]"),
        exceptions=json.loads(o.exceptions_json or "[]"),
        confidence_score=o.confidence_score,
        evidence_status=o.evidence_status,
        review_status=o.review_status,
        extraction_method=o.extraction_method,
        created_at=o.created_at.isoformat(),
        document_title=o.document.title if o.document else None,
        circular_number=o.document.circular_number if o.document else None,
        evidence_span=span_resp
    )

@router.get("/", response_model=ObligationListResponse)
def list_obligations(
    document_id: Optional[int] = None,
    review_status: Optional[str] = None,
    entity: Optional[str] = None,
    search: Optional[str] = None,
    has_deadline: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Obligation)

    if document_id:
        query = query.filter(Obligation.document_id == document_id)

    if review_status:
        query = query.filter(Obligation.review_status == review_status)

    if entity:
        query = query.filter(Obligation.responsible_entity.ilike(f"%{entity.strip()}%"))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Obligation.obligation_text.ilike(term)) |
            (Obligation.obligation_code.ilike(term)) |
            (Obligation.required_action.ilike(term))
        )

    if has_deadline is True:
        query = query.filter(Obligation.deadline.isnot(None))
    elif has_deadline is False:
        query = query.filter(Obligation.deadline.is_(None))

    total = query.count()
    obls = query.order_by(Obligation.id.asc()).offset(skip).limit(limit).all()

    return ObligationListResponse(
        total=total,
        items=[format_obligation_response(o) for o in obls]
    )

@router.get("/{obligation_id}", response_model=ObligationResponse)
def get_obligation(
    obligation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    obl = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obl:
        raise HTTPException(status_code=404, detail="Obligation not found.")

    return format_obligation_response(obl)

@router.put("/{obligation_id}/review", response_model=ObligationResponse)
def review_obligation(
    obligation_id: int,
    req: ObligationReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "compliance_officer", "admin"]))
):
    obl = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obl:
        raise HTTPException(status_code=404, detail="Obligation not found.")

    previous_values = {
        "review_status": obl.review_status,
        "responsible_entity": obl.responsible_entity,
        "required_action": obl.required_action,
        "deadline": obl.deadline
    }

    updated_values = {}

    if req.action == "approved":
        obl.review_status = "approved"
    elif req.action == "rejected":
        obl.review_status = "rejected"
    elif req.action == "corrected":
        obl.review_status = "corrected"
        if req.responsible_entity is not None:
            obl.responsible_entity = req.responsible_entity.strip() or None
            updated_values["responsible_entity"] = obl.responsible_entity
        if req.required_action is not None:
            obl.required_action = req.required_action.strip()
            updated_values["required_action"] = obl.required_action
        if req.deadline is not None:
            obl.deadline = req.deadline.strip() or None
            updated_values["deadline"] = obl.deadline

    # Record Review
    review_entry = ReviewRecord(
        obligation_id=obl.id,
        reviewer_id=current_user.id,
        action=req.action,
        previous_values_json=json.dumps(previous_values),
        updated_values_json=json.dumps(updated_values),
        comments=req.comments
    )
    db.add(review_entry)
    db.commit()
    db.refresh(obl)

    AuditService.log(
        db,
        action=f"obligation_{req.action}",
        resource_type="obligation",
        resource_id=str(obl.id),
        user_id=current_user.id,
        details={
            "obligation_code": obl.obligation_code,
            "action": req.action,
            "comments": req.comments
        }
    )

    return format_obligation_response(obl)
