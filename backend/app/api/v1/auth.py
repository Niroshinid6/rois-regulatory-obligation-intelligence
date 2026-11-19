from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, revoke_access_token
from app.core.dependencies import get_current_user, security_scheme
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact your system administrator."
        )

    access_token = create_access_token(subject=user.id, role=user.role)

    # Log successful login
    AuditService.log(
        db,
        action="user_login",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
        details={"email": user.email, "role": user.role}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoke_access_token(credentials.credentials, db)
    AuditService.log(
        db,
        action="user_logout",
        resource_type="user",
        resource_id=str(current_user.id),
        user_id=current_user.id
    )
    return {"message": "Successfully logged out from ROIS session."}
