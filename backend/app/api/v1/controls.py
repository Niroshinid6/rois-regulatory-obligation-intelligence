from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.control import ControlCategory, ObligationControl
from app.models.obligation import Obligation
from app.schemas.control import ControlCategoryResponse, ObligationControlResponse, MappingReviewRequest
from app.services.audit_service import AuditService

router = APIRouter(prefix="/controls", tags=["Compliance Controls"])

@router.get("/categories", response_model=List[ControlCategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cats = db.query(ControlCategory).filter(ControlCategory.is_active == True).all()
    return cats

@router.post("/categories", response_model=ControlCategoryResponse)
def create_category(
    code: str,
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "compliance_officer"]))
):
    existing = db.query(ControlCategory).filter(ControlCategory.code == code.strip().upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Control category with this code already exists.")

    new_cat = ControlCategory(
        code=code.strip().upper(),
        name=name.strip(),
        description=description.strip() if description else None,
        is_active=True
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)

    AuditService.log(
        db,
        action="control_category_created",
        resource_type="control_category",
        resource_id=str(new_cat.id),
        user_id=current_user.id,
        details={"code": new_cat.code, "name": new_cat.name}
    )

    return new_cat

@router.get("/mappings", response_model=List[ObligationControlResponse])
def list_mappings(
    obligation_id: Optional[int] = None,
    control_category_id: Optional[int] = None,
    review_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ObligationControl)
    if obligation_id:
        query = query.filter(ObligationControl.obligation_id == obligation_id)
    if control_category_id:
        query = query.filter(ObligationControl.control_category_id == control_category_id)
    if review_status:
        query = query.filter(ObligationControl.review_status == review_status)

    mappings = query.all()
    results = []
    for m in mappings:
        results.append(ObligationControlResponse(
            id=m.id,
            obligation_id=m.obligation_id,
            control_category_id=m.control_category_id,
            category_code=m.control_category.code if m.control_category else "",
            category_name=m.control_category.name if m.control_category else "",
            rationale=m.rationale,
            mapping_method=m.mapping_method,
            review_status=m.review_status,
            obligation_code=m.obligation.obligation_code if m.obligation else "",
            obligation_text=m.obligation.obligation_text if m.obligation else ""
        ))
    return results

@router.post("/mappings", response_model=ObligationControlResponse)
def create_mapping(
    obligation_id: int,
    control_category_id: int,
    rationale: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "compliance_officer", "admin"]))
):
    obl = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    cat = db.query(ControlCategory).filter(ControlCategory.id == control_category_id).first()
    if not obl or not cat:
        raise HTTPException(status_code=404, detail="Obligation or Control Category not found.")

    mapping = ObligationControl(
        obligation_id=obligation_id,
        control_category_id=control_category_id,
        rationale=rationale.strip(),
        mapping_method="reviewer_assigned",
        review_status="approved",
        reviewed_by=current_user.id,
        reviewed_at=datetime.now(timezone.utc)
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    AuditService.log(
        db,
        action="control_mapping_created",
        resource_type="obligation_control",
        resource_id=str(mapping.id),
        user_id=current_user.id,
        details={"obligation_code": obl.obligation_code, "control_code": cat.code}
    )

    return ObligationControlResponse(
        id=mapping.id,
        obligation_id=mapping.obligation_id,
        control_category_id=mapping.control_category_id,
        category_code=cat.code,
        category_name=cat.name,
        rationale=mapping.rationale,
        mapping_method=mapping.mapping_method,
        review_status=mapping.review_status,
        obligation_code=obl.obligation_code,
        obligation_text=obl.obligation_text
    )

@router.put("/mappings/{mapping_id}", response_model=ObligationControlResponse)
def update_mapping(
    mapping_id: int,
    req: MappingReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["reviewer", "compliance_officer", "admin"]))
):
    mapping = db.query(ObligationControl).filter(ObligationControl.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found.")

    mapping.review_status = req.review_status
    if req.rationale:
        mapping.rationale = req.rationale.strip()

    mapping.reviewed_by = current_user.id
    mapping.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mapping)

    AuditService.log(
        db,
        action="control_mapping_reviewed",
        resource_type="obligation_control",
        resource_id=str(mapping.id),
        user_id=current_user.id,
        details={"review_status": mapping.review_status}
    )

    return ObligationControlResponse(
        id=mapping.id,
        obligation_id=mapping.obligation_id,
        control_category_id=mapping.control_category_id,
        category_code=mapping.control_category.code if mapping.control_category else "",
        category_name=mapping.control_category.name if mapping.control_category else "",
        rationale=mapping.rationale,
        mapping_method=mapping.mapping_method,
        review_status=mapping.review_status,
        obligation_code=mapping.obligation.obligation_code if mapping.obligation else "",
        obligation_text=mapping.obligation.obligation_text if mapping.obligation else ""
    )
