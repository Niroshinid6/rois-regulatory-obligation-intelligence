import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.obligation import Obligation, ObligationChange, Comparison
from app.models.control import ObligationControl, ControlCategory
from app.schemas.dashboard import DashboardMetricsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_docs = db.query(Document).count()
    processed_docs = db.query(Document).filter(Document.status == "processed").count()

    total_obls = db.query(Obligation).count()
    pending_reviews = db.query(Obligation).filter(Obligation.review_status == "pending").count()
    approved_obls = db.query(Obligation).filter(Obligation.review_status == "approved").count()

    new_obls = db.query(ObligationChange).filter(ObligationChange.change_type == "new").count()
    mod_obls = db.query(ObligationChange).filter(ObligationChange.change_type == "modified").count()
    ret_obls = db.query(ObligationChange).filter(ObligationChange.change_type == "retired").count()

    impacted_controls = db.query(ObligationControl.control_category_id).distinct().count()

    recent_docs_query = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    recent_docs = [
        {
            "id": d.id,
            "title": d.title,
            "circular_number": d.circular_number,
            "regulator": d.regulator,
            "publication_date": d.publication_date,
            "status": d.status,
            "page_count": d.page_count,
            "obligation_count": len(d.obligations)
        }
        for d in recent_docs_query
    ]

    recent_obls_query = db.query(Obligation).order_by(Obligation.created_at.desc()).limit(6).all()
    recent_obls = [
        {
            "id": o.id,
            "obligation_code": o.obligation_code,
            "document_title": o.document.title if o.document else "",
            "circular_number": o.document.circular_number if o.document else "",
            "source_page": o.source_page,
            "responsible_entity": o.responsible_entity,
            "required_action": o.required_action,
            "deadline": o.deadline,
            "review_status": o.review_status,
            "confidence_score": o.confidence_score
        }
        for o in recent_obls_query
    ]

    recent_changes_query = db.query(ObligationChange).order_by(ObligationChange.id.desc()).limit(6).all()
    recent_changes = []
    for c in recent_changes_query:
        recent_changes.append({
            "id": c.id,
            "change_type": c.change_type,
            "change_explanation": c.change_explanation,
            "comparison_id": c.comparison_id,
            "human_verified": c.human_verified,
            "current_code": c.current_obligation.obligation_code if c.current_obligation else None,
            "previous_code": c.previous_obligation.obligation_code if c.previous_obligation else None
        })

    pending_items_query = db.query(Obligation).filter(Obligation.review_status == "pending").order_by(Obligation.created_at.desc()).limit(6).all()
    pending_items = [
        {
            "id": p.id,
            "obligation_code": p.obligation_code,
            "document_title": p.document.title if p.document else "",
            "circular_number": p.document.circular_number if p.document else "",
            "source_page": p.source_page,
            "responsible_entity": p.responsible_entity,
            "required_action": p.required_action,
            "confidence_score": p.confidence_score
        }
        for p in pending_items_query
    ]

    return DashboardMetricsResponse(
        total_documents=total_docs,
        processed_documents=processed_docs,
        total_obligations=total_obls,
        pending_reviews=pending_reviews,
        approved_obligations=approved_obls,
        new_obligations=new_obls,
        modified_obligations=mod_obls,
        retired_obligations=ret_obls,
        impacted_controls_count=impacted_controls,
        recent_documents=recent_docs,
        recent_obligations=recent_obls,
        recent_changes=recent_changes,
        pending_review_items=pending_items
    )
