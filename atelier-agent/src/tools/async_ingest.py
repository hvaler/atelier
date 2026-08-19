"""GCS and Eventarc asynchronous ingestion pipeline (ADR-004, ADR-006)."""

import logging
import uuid

import cv2
import numpy as np

from src.config import settings
from src.models.critique import CritiqueRequest
from src.models.digest import GcsEventPayload, GcsProcessingResponse
from src.models.memory import ExerciseRecord
from src.tools.critique import generate_pedagogical_critique
from src.tools.geometry import analyze_geometry, decode_image_base64
from src.tools.memory import memory_repo
from src.tools.pre_router import classify_drawing

logger = logging.getLogger(__name__)


#: Refused outright rather than handed to OpenCV.
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

#: A drawing photographed on a phone is a couple of megabytes. Twenty is a stranger.
MAX_OBJECT_BYTES = 20 * 1024 * 1024


def download_drawing_from_gcs(bucket: str, name: str) -> np.ndarray:
    """
    Fetch the object the Eventarc trigger is telling us about.

    This function did not exist. When the event carried no inline base64 — which a real
    CloudEvent never does — the pipeline drew four `cv2.line()` calls on a blank canvas and
    analysed *that*, then filed the result as the student's drawing. Two different uploads
    produced the identical 0.62 degrees, and `docs/EVIDENCE.md` published that number as the
    measurement of a specific PNG. The bucket was never read; `google-cloud-storage` was
    declared as a dependency and imported nowhere.

    Failures raise. The endpoint turns that into a 400, which is the honest answer: an ingestion
    that cannot read the drawing has nothing to say about it.
    """
    from google.cloud import storage

    blob = storage.Client(project=settings.gcp_project).bucket(bucket).get_blob(name)
    if blob is None:
        raise ValueError(f"gs://{bucket}/{name} does not exist or is not readable.")
    if blob.size and blob.size > MAX_OBJECT_BYTES:
        raise ValueError(f"gs://{bucket}/{name} is {blob.size} bytes; the limit is {MAX_OBJECT_BYTES}.")
    if blob.content_type and blob.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"gs://{bucket}/{name} is {blob.content_type}, which is not an image.")

    buffer = np.frombuffer(blob.download_as_bytes(), dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"gs://{bucket}/{name} could not be decoded as an image.")

    logger.info("Ingested gs://%s/%s (%d bytes)", bucket, name, blob.size or 0)
    return image


def process_gcs_upload_event(event: GcsEventPayload) -> GcsProcessingResponse:
    """Process a drawing uploaded to GCS inbox triggered via Eventarc (google.cloud.storage.object.v1.finalized)."""
    # 1. Parse student_id from object name '{student_id}/{filename}'
    parts = event.name.split("/")
    student_id = parts[0] if len(parts) > 1 else "young-tester-01"

    student = memory_repo.get_student(student_id)
    if not student:
        raise ValueError(f"Student profile '{student_id}' does not exist.")

    # 2. The drawing. Inline base64 only when a caller supplied it directly (tests, the
    #    synchronous path); otherwise the object named by the event, read from the bucket.
    image = (
        decode_image_base64(event.image_base64)
        if event.image_base64
        else download_drawing_from_gcs(event.bucket, event.name)
    )

    # 3. The gate, before anything expensive. Nobody is watching this path — a file lands in a
    #    bucket and the pipeline runs — so this is exactly where a photograph that is not a
    #    drawing would otherwise be measured, critiqued and filed under a child's name.
    gate = classify_drawing(cv2.imencode(".png", image)[1].tobytes())
    if not gate.is_exercise:
        raise ValueError(
            f"gs://{event.bucket}/{event.name} is not a perspective exercise: {gate.reasoning}"
        )

    # 4. Deterministic geometry analysis (ADR-001). The gate's k wins when it looked at the
    #    drawing; the profile level is only the fallback.
    k_points = gate.recommended_k if gate.source == "vertex" else (1 if student.level == "beginner" else 2)
    geom_result = analyze_geometry(
        image=image,
        k_points=k_points,
        generate_overlay_flag=True,
    )

    # 5. Generate pedagogical critique (Gemini 3.5 Flash on Vertex AI)
    critique_req = CritiqueRequest(
        geometry=geom_result,
        student=student,
        student_intent="Automated GCS async ingestion",
        use_cache=False,
    )
    critique_resp = generate_pedagogical_critique(critique_req)

    # 6. Persist to append-only memory (ADR-005)
    exercise_id = f"ex-gcs-{uuid.uuid4().hex[:8]}"
    record = ExerciseRecord(
        exercise_id=exercise_id,
        student_id=student_id,
        image_uri=f"gs://{event.bucket}/{event.name}",
        source="folder",
        student_intent="GCS Inbox upload",
        geometry_analysis=geom_result,
        critique=critique_resp.critique,
    )
    memory_repo.save_exercise(record)

    return GcsProcessingResponse(
        status="processed",
        exercise_id=exercise_id,
        student_id=student_id,
        student_name=student.name,
        k_detected=geom_result.k_detected,
        avg_convergence_error_deg=geom_result.avg_convergence_error_deg,
        critique_headline=critique_resp.critique.headline,
    )
