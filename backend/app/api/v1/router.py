from fastapi import APIRouter
from app.api.v1 import (
    auth,
    users,
    dashboard,
    documents,
    obligations,
    evidence,
    comparisons,
    controls,
    reports,
    audit
)

api_router = APIRouter()

@api_router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "online",
        "system": "ROIS — Regulatory Obligation Intelligence System",
        "scope": "IFSCA Regulatory Scope",
        "tagline": "Every compliance obligation, traced to the exact sentence that created it.",
        "version": "1.0.0"
    }

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(documents.router)
api_router.include_router(obligations.router)
api_router.include_router(evidence.router)
api_router.include_router(comparisons.router)
api_router.include_router(controls.router)
api_router.include_router(reports.router)
api_router.include_router(audit.router)
