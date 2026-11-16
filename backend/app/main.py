import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ROIS transforms complex financial regulatory documents into structured, traceable and actionable compliance intelligence.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": "Welcome to ROIS — Regulatory Obligation Intelligence System",
        "tagline": "Every compliance obligation, traced to the exact sentence that created it.",
        "documentation": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
