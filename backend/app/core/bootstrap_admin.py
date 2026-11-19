from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import Role, User


def bootstrap_admin() -> None:
    if settings.ROIS_ENV.lower() != "production":
        raise RuntimeError("Administrator bootstrap is intended for production only.")

    email = settings.BOOTSTRAP_ADMIN_EMAIL.strip().lower()
    password = settings.BOOTSTRAP_ADMIN_PASSWORD
    full_name = settings.BOOTSTRAP_ADMIN_FULL_NAME.strip()

    if not email or "@" not in email:
        raise RuntimeError("BOOTSTRAP_ADMIN_EMAIL is required.")
    if len(password) < 12:
        raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD must contain at least 12 characters.")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_role = db.query(Role).filter(Role.name == "admin").first()
        if not existing_role:
            db.add(Role(name="admin", description="System administrator", permissions_json='["*"]'))
            db.flush()

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print("Configured administrator already exists.")
            return

        db.add(
            User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name or "ROIS System Administrator",
                role="admin",
                is_active=True,
            )
        )
        db.commit()
        print("Production administrator created.")
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_admin()
