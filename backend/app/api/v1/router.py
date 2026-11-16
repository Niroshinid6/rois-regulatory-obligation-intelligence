from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "online",
        "system": "ROIS — Regulatory Obligation Intelligence System",
        "scope": "IFSCA Regulatory Scope",
        "tagline": "Every compliance obligation, traced to the exact sentence that created it.",
        "phase": "Phase A Initialized"
    }
