import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.obligation import Obligation
from app.models.document import DocumentPage

router = APIRouter(prefix="/evidence", tags=["Evidence Verification"])

@router.get("/{obligation_id}")
def get_evidence_details(
    obligation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    obl = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obl:
        raise HTTPException(status_code=404, detail="Obligation not found.")

    doc = obl.document
    if not doc:
        raise HTTPException(status_code=404, detail="Associated document not found.")

    # Retrieve page text and bounding boxes for the exact source page
    page = db.query(DocumentPage).filter(
        DocumentPage.document_id == doc.id,
        DocumentPage.page_number == obl.source_page
    ).first()

    page_data = None
    if page:
        page_data = {
            "page_number": page.page_number,
            "char_count": page.char_count,
            "word_count": page.word_count,
            "has_selectable_text": page.has_selectable_text,
            "extracted_text": page.extracted_text,
            "bounding_boxes": json.loads(page.bounding_boxes_json or "[]")
        }

    evidence_span_data = None
    if obl.evidence_span:
        evidence_span_data = {
            "id": obl.evidence_span.id,
            "page_number": obl.evidence_span.page_number,
            "exact_text": obl.evidence_span.exact_text,
            "char_start": obl.evidence_span.char_start,
            "char_end": obl.evidence_span.char_end,
            "bounding_box": json.loads(obl.evidence_span.bounding_box_json or "{}"),
            "confidence": obl.evidence_span.confidence
        }

    reviews = [
        {
            "id": r.id,
            "action": r.action,
            "reviewer_name": r.reviewer.full_name if r.reviewer else "Unknown",
            "reviewer_email": r.reviewer.email if r.reviewer else "",
            "comments": r.comments,
            "created_at": r.created_at.isoformat(),
            "previous_values": json.loads(r.previous_values_json or "{}"),
            "updated_values": json.loads(r.updated_values_json or "{}")
        }
        for r in obl.reviews
    ]

    controls = [
        {
            "id": c.id,
            "category_code": c.control_category.code,
            "category_name": c.control_category.name,
            "rationale": c.rationale,
            "review_status": c.review_status,
            "mapping_method": c.mapping_method
        }
        for c in obl.controls
    ]

    return {
        "obligation": {
            "id": obl.id,
            "obligation_code": obl.obligation_code,
            "document_id": obl.document_id,
            "source_page": obl.source_page,
            "obligation_text": obl.obligation_text,
            "responsible_entity": obl.responsible_entity,
            "required_action": obl.required_action,
            "deadline": obl.deadline,
            "conditions": json.loads(obl.conditions_json or "[]"),
            "exceptions": json.loads(obl.exceptions_json or "[]"),
            "confidence_score": obl.confidence_score,
            "evidence_status": obl.evidence_status,
            "review_status": obl.review_status,
            "extraction_method": obl.extraction_method,
            "created_at": obl.created_at.isoformat()
        },
        "document": {
            "id": doc.id,
            "title": doc.title,
            "circular_number": doc.circular_number,
            "regulator": doc.regulator,
            "publication_date": doc.publication_date,
            "page_count": doc.page_count,
            "pdf_url": f"/api/v1/documents/{doc.id}/pdf"
        },
        "source_page": page_data,
        "evidence_span": evidence_span_data,
        "reviews": reviews,
        "controls": controls
    }
