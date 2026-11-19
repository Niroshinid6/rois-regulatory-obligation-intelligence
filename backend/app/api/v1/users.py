from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, Role
from app.schemas.auth import UserResponse, UserCreate, UserUpdate, RoleResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "management"]))
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat()
        )
        for u in users
    ]

@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    roles = db.query(Role).all()
    return roles

@router.post("/", response_model=UserResponse)
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email address already exists.")

    new_user = User(
        email=req.email.lower().strip(),
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=req.role,
        is_active=req.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    AuditService.log(
        db,
        action="user_created",
        resource_type="user",
        resource_id=str(new_user.id),
        user_id=current_user.id,
        details={"created_email": new_user.email, "role": new_user.role}
    )

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat()
    )

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    if req.full_name is not None:
        target_user.full_name = req.full_name
    if req.role is not None:
        target_user.role = req.role
    if req.is_active is not None:
        target_user.is_active = req.is_active
    if req.password:
        target_user.hashed_password = get_password_hash(req.password)

    db.commit()
    db.refresh(target_user)

    AuditService.log(
        db,
        action="user_updated",
        resource_type="user",
        resource_id=str(target_user.id),
        user_id=current_user.id,
        details={"updated_fields": list(req.model_dump(exclude_unset=True).keys())}
    )

    return UserResponse(
        id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=target_user.role,
        is_active=target_user.is_active,
        created_at=target_user.created_at.isoformat()
    )
