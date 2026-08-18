"""GCS and Eventarc asynchronous ingestion pipeline (ADR-004, ADR-006)."""

import uuid

import cv2
import numpy as np

from src.models.critique import CritiqueRequest
from src.models.digest import GcsEventPayload, GcsProcessingResponse
from src.models.memory import ExerciseRecord
from src.tools.critique import generate_pedagogical_critique
from src.tools.geometry import analyze_geometry, decode_image_base64
from src.tools.memory import memory_repo


def create_mock_drawing_for_ingest(k: int = 1) -> np.ndarray:
    """Create a default sample perspective drawing when receiving a purely simulated cloud event."""
    canvas = np.ones((500, 700, 3), dtype=np.uint8) * 245
    if k == 1:
        # 1-point converging lines towards center VP (350, 200)
        vp = (350, 200)
        cv2.line(canvas, (100, 450), vp, (30, 30, 30), 2)
        cv2.line(canvas, (600, 450), vp, (30, 30, 30), 2)
        cv2.line(canvas, (200, 400), vp, (30, 30, 30), 2)
        cv2.line(canvas, (500, 400), vp, (30, 30, 30), 2)
    else:
        # 2-point converging lines towards F1 (100, 200) and F2 (600, 200)
        cv2.line(canvas, (350, 350), (100, 200), (30, 30, 30), 2)
        cv2.line(canvas, (350, 450), (100, 200), (30, 30, 30), 2)
        cv2.line(canvas, (350, 350), (600, 200), (30, 30, 30), 2)
        cv2.line(canvas, (350, 450), (600, 200), (30, 30, 30), 2)
    return canvas


def process_gcs_upload_event(event: GcsEventPayload) -> GcsProcessingResponse:
    """Process a drawing uploaded to GCS inbox triggered via Eventarc (google.cloud.storage.object.v1.finalized)."""
    # 1. Parse student_id from object name '{student_id}/{filename}'
    parts = event.name.split("/")
    student_id = parts[0] if len(parts) > 1 else "young-tester-01"

    student = memory_repo.get_student(student_id)
    if not student:
        raise ValueError(f"Student profile '{student_id}' does not exist.")

    # 2. Extract or decode image
    if event.image_base64:
        image = decode_image_base64(event.image_base64)
    else:
        k_val = 1 if student.level == "beginner" else 2
        image = create_mock_drawing_for_ingest(k=k_val)

    # 3. Deterministic geometry analysis (ADR-001)
    k_points = 1 if student.level == "beginner" else 2
    geom_result = analyze_geometry(
        image=image,
        k_points=k_points,
        generate_overlay_flag=True,
    )

    # 4. Generate pedagogical critique (Gemini 3.5 Flash on Vertex AI)
    critique_req = CritiqueRequest(
        geometry=geom_result,
        student=student,
        student_intent="Automated GCS async ingestion",
        use_cache=True,
    )
    critique_resp = generate_pedagogical_critique(critique_req)

    # 5. Persist to append-only memory (ADR-005)
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
