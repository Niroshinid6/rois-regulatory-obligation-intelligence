import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.document import Document
from app.models.obligation import Comparison, ObligationChange, Obligation
from app.schemas.comparison import ComparisonCreate, ComparisonResponse, ObligationChangeResponse
from app.schemas.obligation import ObligationResponse
from app.services.version_comparator import VersionComparator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/comparisons", tags=["Version Comparison"])

def format_change_response(c: ObligationChange) -> ObligationChangeResponse:
    prev_resp = None
    if c.previous_obligation:
        prev_resp = ObligationResponse(
            id=c.previous_obligation.id,
            obligation_code=c.previous_obligation.obligation_code,
            document_id=c.previous_obligation.document_id,
            source_page=c.previous_obligation.source_page,
            obligation_text=c.previous_obligation.obligation_text,
            responsible_entity=c.previous_obligation.responsible_entity,
            required_action=c.previous_obligation.required_action,
            deadline=c.previous_obligation.deadline,
            conditions=json.loads(c.previous_obligation.conditions_json or "[]"),
            exceptions=json.loads(c.previous_obligation.exceptions_json or "[]"),
            confidence_score=c.previous_obligation.confidence_score,
            evidence_status=c.previous_obligation.evidence_status,
            review_status=c.previous_obligation.review_status,
            extraction_method=c.previous_obligation.extraction_method,
            created_at=c.previous_obligation.created_at.isoformat()
        )

    curr_resp = None
    if c.current_obligation:
        curr_resp = ObligationResponse(
            id=c.current_obligation.id,
            obligation_code=c.current_obligation.obligation_code,
            document_id=c.current_obligation.document_id,
            source_page=c.current_obligation.source_page,
            obligation_text=c.current_obligation.obligation_text,
            responsible_entity=c.current_obligation.responsible_entity,
            required_action=c.current_obligation.required_action,
            deadline=c.current_obligation.deadline,
            conditions=json.loads(c.current_obligation.conditions_json or "[]"),
            exceptions=json.loads(c.current_obligation.exceptions_json or "[]"),
            confidence_score=c.current_obligation.confidence_score,
            evidence_status=c.current_obligation.evidence_status,
            review_status=c.current_obligation.review_status,
            extraction_method=c.current_obligation.extraction_method,
            created_at=c.current_obligation.created_at.isoformat()
        )

    return ObligationChangeResponse(
        id=c.id,
        comparison_id=c.comparison_id,
        previous_obligation_id=c.previous_obligation_id,
        current_obligation_id=c.current_obligation_id,
        change_type=c.change_type,
        change_explanation=c.change_explanation,
        diff_details=json.loads(c.diff_details_json or "{}"),
        human_verified=c.human_verified,
        previous_obligation=prev_resp,
        current_obligation=curr_resp
    )

@router.get("/", response_model=List[ComparisonResponse])
def list_comparisons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comps = db.query(Comparison).order_by(Comparison.created_at.desc()).all()
    results = []
    for c in comps:
        results.append(ComparisonResponse(
            id=c.id,
            title=c.title,
            base_document_id=c.base_document_id,
            target_document_id=c.target_document_id,
            base_document_title=c.base_document.title if c.base_document else None,
            base_circular_number=c.base_document.circular_number if c.base_document else None,
            target_document_title=c.target_document.title if c.target_document else None,
            target_circular_number=c.target_document.circular_number if c.target_document else None,
            status=c.status,
            created_at=c.created_at.isoformat(),
            changes=[format_change_response(ch) for ch in c.changes]
        ))
    return results

@router.post("/", response_model=ComparisonResponse)
def create_comparison(
    req: ComparisonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["compliance_officer", "admin"]))
):
    base_doc = db.query(Document).filter(Document.id == req.base_document_id).first()
    target_doc = db.query(Document).filter(Document.id == req.target_document_id).first()

    if not base_doc or not target_doc:
        raise HTTPException(status_code=404, detail="One or both regulatory documents could not be found.")

    if base_doc.id == target_doc.id:
        raise HTTPException(status_code=400, detail="Cannot compare a document against itself. Please select two distinct circulars.")

    title = req.title or f"Regulatory Delta: {base_doc.circular_number or base_doc.title} vs {target_doc.circular_number or target_doc.title}"

    comp = Comparison(
        title=title,
        base_document_id=base_doc.id,
        target_document_id=target_doc.id,
        created_by=current_user.id,
        status="completed"
    )
    db.add(comp)
    db.flush()

    base_raw = [
        {
            "id": o.id,
            "obligation_text": o.obligation_text,
            "required_action": o.required_action,
            "responsible_entity": o.responsible_entity,
            "deadline": o.deadline,
            "conditions": json.loads(o.conditions_json or "[]"),
            "exceptions": json.loads(o.exceptions_json or "[]"),
            "source_page": o.source_page,
        }
        for o in base_doc.obligations
    ]
    target_raw = [
        {
            "id": o.id,
            "obligation_text": o.obligation_text,
            "required_action": o.required_action,
            "responsible_entity": o.responsible_entity,
            "deadline": o.deadline,
            "conditions": json.loads(o.conditions_json or "[]"),
            "exceptions": json.loads(o.exceptions_json or "[]"),
            "source_page": o.source_page,
        }
        for o in target_doc.obligations
    ]

    diff_results = VersionComparator.compare_documents(base_raw, target_raw)

    saved_changes = []
    for d in diff_results:
        change = ObligationChange(
            comparison_id=comp.id,
            previous_obligation_id=d["previous_obligation_id"],
            current_obligation_id=d["current_obligation_id"],
            change_type=d["change_type"],
            change_explanation=d["change_explanation"],
            diff_details_json=json.dumps(d["diff_details"]),
            human_verified=d["human_verified"]
        )
        db.add(change)
        db.flush()
        saved_changes.append(change)

    db.commit()
    db.refresh(comp)

    AuditService.log(
        db,
        action="comparison_created",
        resource_type="comparison",
        resource_id=str(comp.id),
        user_id=current_user.id,
        details={
            "base_doc": base_doc.title,
            "target_doc": target_doc.title,
            "changes_detected": len(saved_changes)
        }
    )

    return ComparisonResponse(
        id=comp.id,
        title=comp.title,
        base_document_id=comp.base_document_id,
        target_document_id=comp.target_document_id,
        base_document_title=base_doc.title,
        base_circular_number=base_doc.circular_number,
        target_document_title=target_doc.title,
        target_circular_number=target_doc.circular_number,
        status=comp.status,
        created_at=comp.created_at.isoformat(),
        changes=[format_change_response(ch) for ch in saved_changes]
    )

@router.get("/{comparison_id}", response_model=ComparisonResponse)
def get_comparison(
    comparison_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = db.query(Comparison).filter(Comparison.id == comparison_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Comparison record not found.")

    return ComparisonResponse(
        id=c.id,
        title=c.title,
        base_document_id=c.base_document_id,
        target_document_id=c.target_document_id,
        base_document_title=c.base_document.title if c.base_document else None,
        base_circular_number=c.base_document.circular_number if c.base_document else None,
        target_document_title=c.target_document.title if c.target_document else None,
        target_circular_number=c.target_document.circular_number if c.target_document else None,
        status=c.status,
        created_at=c.created_at.isoformat(),
        changes=[format_change_response(ch) for ch in c.changes]
    )

@router.put("/changes/{change_id}/verify", response_model=ObligationChangeResponse)
def verify_change(
    change_id: int,
    verified_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "compliance_officer", "admin"]))
):
    change = db.query(ObligationChange).filter(ObligationChange.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change item not found.")

    if verified_type:
        change.change_type = verified_type

    change.human_verified = True
    change.verified_by = current_user.id
    change.verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(change)

    AuditService.log(
        db,
        action="change_verified",
        resource_type="obligation_change",
        resource_id=str(change.id),
        user_id=current_user.id,
        details={"new_status": change.change_type}
    )

    return format_change_response(change)
