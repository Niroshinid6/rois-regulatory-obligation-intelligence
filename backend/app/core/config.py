from pathlib import Path
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEVELOPMENT_SECRET = "rois-dev-secret-key-change-in-production"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=PROJECT_ROOT / ".env",
        extra="allow",
    )

    PROJECT_NAME: str = "ROIS — Regulatory Obligation Intelligence System"
    API_V1_PREFIX: str = "/api/v1"
    ROIS_ENV: str = "development"
    SECRET_KEY: str = DEVELOPMENT_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"
    ROIS_DEMO_ADMIN_PASSWORD: str = ""
    ROIS_DEMO_COMPLIANCE_PASSWORD: str = ""
    ROIS_DEMO_REVIEWER_PASSWORD: str = ""
    ROIS_DEMO_MANAGEMENT_PASSWORD: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./rois.db"

    # Uploads & Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    BOOTSTRAP_ADMIN_EMAIL: str = ""
    BOOTSTRAP_ADMIN_PASSWORD: str = ""
    BOOTSTRAP_ADMIN_FULL_NAME: str = "ROIS System Administrator"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def require_production_secret(self):
        env = self.ROIS_ENV.lower()
        if env != "test" and (
            self.SECRET_KEY == DEVELOPMENT_SECRET or len(self.SECRET_KEY) < 32
            or self.SECRET_KEY.lower().startswith(("replace-", "change-"))
        ):
            raise ValueError(
                "Non-test environments require a unique SECRET_KEY of at least 32 characters."
            )
        if env == "production":
            database_url = self.DATABASE_URL.lower()
            if database_url.startswith("sqlite"):
                raise ValueError("Production requires PostgreSQL; SQLite is not supported.")
            if not database_url.startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
                raise ValueError("Production DATABASE_URL must be a PostgreSQL connection URL.")
            cors_origins = [origin.strip().lower() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            if not cors_origins or any(
                origin.startswith("http://localhost")
                or origin.startswith("http://127.0.0.1")
                or origin == "*"
                for origin in cors_origins
            ):
                raise ValueError("Production CORS_ORIGINS must contain exact HTTPS frontend origins.")
        if env not in {"development", "test", "production"}:
            raise ValueError("ROIS_ENV must be one of: development, test, production.")
        return self

settings = Settings()
