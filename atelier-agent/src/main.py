"""Main entry point for Atelier Agent FastAPI service."""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings

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


@app.get("/")
def root():
    return {
        "message": "Atelier Agent is running.",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
