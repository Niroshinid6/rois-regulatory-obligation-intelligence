import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ROIS — Regulatory Obligation Intelligence System"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "rois-dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rois.db")

    # Uploads & Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_SIZE_MB: int = 25

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
