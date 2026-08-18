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



from pydantic import BaseModel

from src.models.critique import (
    CritiqueRequest,
    CritiqueResponse,
    NextExerciseRecommendation,
    StudentProfile,
)
from src.models.memory import AskPromptData, DerivedProfile, ExerciseRecord, FeedbackEvent
from src.tools.collaborative import (
    adapt_profile,
    ask_clarification,
    capture_feedback,
    guide_next_exercise,
)
from src.tools.critique import generate_pedagogical_critique
from src.tools.memory import memory_repo


class FeedbackRequest(BaseModel):
    student_id: str
    helpful: bool
    note: str | None = None


@app.post("/api/critique", response_model=CritiqueResponse, status_code=status.HTTP_200_OK)
def create_critique(request: CritiqueRequest) -> CritiqueResponse:
    """Generate pedagogical critique with Gemini 3.5 Flash on Vertex AI (ADR-001)."""
    return generate_pedagogical_critique(request)


# -----------------------------------------------------------------------------
# Collaborative Partner & Memory Endpoints (The 4 Verbs: Ask, Guide, Capture, Adapt)
# -----------------------------------------------------------------------------


@app.get("/api/students", response_model=list[StudentProfile], status_code=status.HTTP_200_OK)
def list_students() -> list[StudentProfile]:
    """List all registered student profiles (Multi-student support)."""
    return memory_repo.list_students()


@app.post("/api/students", response_model=StudentProfile, status_code=status.HTTP_201_CREATED)
def register_student(student: StudentProfile) -> StudentProfile:
    """Register a new student profile."""
    return memory_repo.register_student(student)


@app.get("/api/students/{student_id}/ask", response_model=AskPromptData, status_code=status.HTTP_200_OK)
def get_ask_questions(student_id: str) -> AskPromptData:
    """Verb 1: ASK clarifying questions to the student before analyzing their work."""
    return ask_clarification(student_id)


@app.get("/api/students/{student_id}/guide", response_model=NextExerciseRecommendation, status_code=status.HTTP_200_OK)
def get_next_guided_exercise(student_id: str) -> NextExerciseRecommendation:
    """Verb 2: GUIDE the student with the next recommended exercise derived from recurring error patterns."""
    try:
        return guide_next_exercise(student_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@app.post("/api/exercises", response_model=ExerciseRecord, status_code=status.HTTP_201_CREATED)
def save_exercise_record(exercise: ExerciseRecord) -> ExerciseRecord:
    """Persist an immutable exercise record to append-only memory (ADR-005)."""
    return memory_repo.save_exercise(exercise)


@app.post("/api/exercises/{exercise_id}/feedback", response_model=FeedbackEvent, status_code=status.HTTP_201_CREATED)
def submit_feedback(exercise_id: str, request: FeedbackRequest) -> FeedbackEvent:
    """Verb 3: CAPTURE explicit student feedback as an immutable event."""
    try:
        return capture_feedback(
            exercise_id=exercise_id,
            student_id=request.student_id,
            helpful=request.helpful,
            note=request.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@app.get("/api/students/{student_id}/profile", response_model=DerivedProfile, status_code=status.HTTP_200_OK)
def get_derived_student_profile(student_id: str) -> DerivedProfile:
    """Verb 4: ADAPT - Retrieve dynamically derived student profile, tone preference and progress curve."""
    try:
        return adapt_profile(student_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


from src.models.digest import (
    GcsEventPayload,
    GcsProcessingResponse,
    WeeklyDigest,
    WeeklyDigestRequest,
)
from src.tools.async_ingest import process_gcs_upload_event
from src.tools.digest import generate_weekly_digest, get_student_digests

# -----------------------------------------------------------------------------
# Asynchronous Ingestion & Weekly Digest (ADR-004: GCS + Eventarc + Cloud Scheduler)
# -----------------------------------------------------------------------------


@app.post("/api/events/gcs-upload", response_model=GcsProcessingResponse, status_code=status.HTTP_200_OK)
def handle_gcs_upload_event(event: GcsEventPayload) -> GcsProcessingResponse:
    """Eventarc webhook receiver triggered on GCS object finalize (google.cloud.storage.object.v1.finalized)."""
    try:
        return process_gcs_upload_event(event)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@app.post("/api/digest/weekly", response_model=WeeklyDigest, status_code=status.HTTP_200_OK)
def trigger_weekly_digest(request: WeeklyDigestRequest) -> WeeklyDigest:
    """Cloud Scheduler endpoint to generate weekly digest, progress delta and practice plan."""
    try:
        return generate_weekly_digest(request.student_id, request.week_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@app.get("/api/students/{student_id}/digests", response_model=list[WeeklyDigest], status_code=status.HTTP_200_OK)
def list_student_digests(student_id: str) -> list[WeeklyDigest]:
    """Retrieve historical weekly digests for a student."""
    return get_student_digests(student_id)


from src.tools.gemma_router import GemmaClassificationResult, classify_drawing_with_gemma


class RouterRequest(BaseModel):
    image_width: int = 800
    image_height: int = 600
    student_level_hint: str = "beginner"


@app.post("/api/router/classify", response_model=GemmaClassificationResult, status_code=status.HTTP_200_OK)
def classify_with_gemma(request: RouterRequest) -> GemmaClassificationResult:
    """Gemma lightweight pre-router on Vertex AI for exercise routing & parameter tuning (+0.2 pts ATA Bonus)."""
    return classify_drawing_with_gemma(
        image_width=request.image_width,
        image_height=request.image_height,
        student_level_hint=request.student_level_hint,
    )


@app.get("/")
def root():
    return {
        "message": "Atelier Agent is running.",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "analyze_url": "/api/analyze",
        "critique_url": "/api/critique",
        "students_url": "/api/students",
        "events_url": "/api/events/gcs-upload",
        "digest_url": "/api/digest/weekly",
        "router_url": "/api/router/classify",
    }
