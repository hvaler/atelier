"""Main entry point for Atelier Agent FastAPI service."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.models.axonometry import AxonometricAnalysisRequest, AxonometricAnalysisResult
from src.models.dihedral import DihedralAnalysisRequest, DihedralAnalysisResult
from src.models.geometry import GeometryAnalysisRequest, GeometryAnalysisResult
from src.tools.axonometry import analyze_axonometric
from src.tools.dihedral import analyze_dihedral
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
    # Which model, and where it is being asked for. Reported because the alternative was
    # discovering from Cloud Logging that every critique had 404'd for days: the service ran in
    # a region where this model is not published, and the failure was swallowed. A health check
    # that cannot show its own model configuration cannot tell you it is misconfigured.
    gemini_model: str
    gemini_location: str
    #: Which store student history is actually in, so a downgrade to process memory is visible
    #: from outside rather than only in a log line nobody reads.
    memory_backend: str


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
        gemini_model=settings.gemini_model,
        gemini_location=settings.gemini_location,
        memory_backend=memory_repo.backend,
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


@app.post("/api/analyze/axonometric", response_model=AxonometricAnalysisResult, status_code=status.HTTP_200_OK)
def analyze_axonometric_drawing(request: AxonometricAnalysisRequest) -> AxonometricAnalysisResult:
    """
    Measure an axonometric drawing against the fixed axes of its projection system (ADR-001).

    A separate endpoint rather than a flag on /api/analyze, because the two produce genuinely
    different measurements. Conic perspective estimates a vanishing point from the drawing and
    reports deviation from that estimate; axonometry compares against angles that are constants of
    the system. Squeezing both through one response shape would mean a payload where half the
    fields are always null and `convergence_error_deg` measures something that never converges.
    """
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

    try:
        return analyze_axonometric(
            image=image,
            system=request.system,
            receding_angle_deg=request.receding_angle_deg,
            off_axis_threshold_deg=request.off_axis_threshold_deg,
            min_confidence_threshold=request.min_confidence_threshold,
            generate_overlay_image=request.generate_overlay,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@app.post("/api/analyze/dihedral", response_model=DihedralAnalysisResult, status_code=status.HTTP_200_OK)
def analyze_dihedral_drawing(request: DihedralAnalysisRequest) -> DihedralAnalysisResult:
    """
    Measure a Monge plate: two orthographic views against each other, about the ground line (ADR-001).

    The third measurement shape and the third kind of reference. Conic infers its reference with
    RANSAC, axonometric is handed it as a constant, and this one reads it off the page: the ground
    line is a line the student actually drew, so nothing is estimated, but a crooked one skews
    everything measured against it, which is why its tilt is reported as a figure in its own right.
    """
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

    return analyze_dihedral(
        image=image,
        correspondence_tolerance_pct=request.correspondence_tolerance_pct,
        min_confidence_threshold=request.min_confidence_threshold,
        generate_overlay_image=request.generate_overlay,
    )





from pydantic import BaseModel

from src.models.critique import (
    CritiqueRequest,
    CritiqueResponse,
    NextExerciseRecommendation,
    StudentProfile,
)
from src.models.memory import (
    AskPromptData,
    DerivedProfile,
    ExerciseRecord,
    ExerciseSummary,
    FeedbackEvent,
)
from src.tools.collaborative import (
    adapt_profile,
    ask_clarification,
    capture_feedback,
    guide_next_exercise,
)
from src.tools.critique import generate_pedagogical_critique
from src.tools.memory import memory_repo, summarise_exercise


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
def get_ask_questions(student_id: str, language: str = "en") -> AskPromptData:
    """Verb 1: ASK clarifying questions to the student before analyzing their work."""
    return ask_clarification(student_id, language=language)


@app.get("/api/students/{student_id}/guide", response_model=NextExerciseRecommendation, status_code=status.HTTP_200_OK)
def get_next_guided_exercise(student_id: str) -> NextExerciseRecommendation:
    """Verb 2: GUIDE the student with the next recommended exercise derived from recurring error patterns."""
    try:
        return guide_next_exercise(student_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@app.get(
    "/api/students/{student_id}/exercises",
    response_model=list[ExerciseSummary],
    status_code=status.HTTP_200_OK,
)
def list_student_exercises(student_id: str, limit: int = 20) -> list[ExerciseSummary]:
    """
    The student's own history, newest first.

    Summaries rather than records: a stored exercise carries the full analysis of whichever system
    was measured, overlay image included, and twenty of those is a payload no list can use.
    """
    records = memory_repo.get_student_exercises(student_id)
    records = sorted(records, key=lambda r: r.created_at, reverse=True)[: max(1, min(limit, 100))]
    return [summarise_exercise(r) for r in records]


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
@app.post("/api/async/gcs-upload", response_model=GcsProcessingResponse, status_code=status.HTTP_200_OK)
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


from src.tools.pre_router import (
    DrawingGateResult,
    RoutingResult,
    classify_drawing,
    route_from_intent,
)


class RouterRequest(BaseModel):
    """What the router needs: the student's words, and their level as the fallback."""

    student_intent: str | None = None
    student_level_hint: str = "beginner"


@app.post("/api/router/classify", response_model=RoutingResult, status_code=status.HTTP_200_OK)
def classify_drawing_intent(request: RouterRequest) -> RoutingResult:
    """Choose the perspective model from the student's own description, on Gemma 4."""
    return route_from_intent(
        student_intent=request.student_intent,
        student_level=request.student_level_hint,
    )


@app.post("/api/router/gate", response_model=DrawingGateResult, status_code=status.HTTP_200_OK)
def gate_drawing(request: GeometryAnalysisRequest) -> DrawingGateResult:
    """Is this photograph a perspective exercise at all? Gemini 3.5 Flash looks before we measure."""
    if not request.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_base64 must be provided in the request body.",
        )
    import base64

    return classify_drawing(base64.b64decode(request.image_base64))


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
