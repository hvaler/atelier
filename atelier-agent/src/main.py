"""Main entry point for Atelier Agent FastAPI service."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.models.geometry import GeometryAnalysisRequest, GeometryAnalysisResult
from src.tools.geometry import analyze_geometry, decode_image_base64

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Deterministic geometry + Pedagogical critique AI agent for art students",
)

# CORS middleware for Blazor UI frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    gcp_project: str


@app.get("/api/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check() -> HealthResponse:
    """Health check endpoint for Cloud Run and monitoring.

    Note: We explicitly use /api/health to avoid Cloud Run intercepting /healthz.
    """
    return HealthResponse(
        status="healthy",
        service="atelier-agent",
        version=settings.app_version,
        environment=settings.environment,
        gcp_project=settings.gcp_project,
    )


@app.post("/api/analyze", response_model=GeometryAnalysisResult, status_code=status.HTTP_200_OK)
def analyze_drawing(request: GeometryAnalysisRequest) -> GeometryAnalysisResult:
    """Analyze a perspective drawing deterministically using OpenCV (ADR-001)."""
    if not request.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_base64 must be provided in the request body.",
        )

    try:
        image = decode_image_base64(request.image_base64)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format: {e!s}",
        ) from e

    result = analyze_geometry(
        image=image,
        k_points=request.k_points,
        min_confidence_threshold=request.min_confidence_threshold,
        generate_overlay_flag=request.generate_overlay,
    )
    return result


@app.get("/")
def root():
    return {
        "message": "Atelier Agent is running.",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "analyze_url": "/api/analyze",
    }
