"""Pedagogical critique service using Gemini Flash via Vertex AI (ADR-001 & PAT-006)."""

import base64
import hashlib
import json
import logging
from pathlib import Path

from src.config import settings
from src.models.critique import (
    CritiqueLlmOutput,
    CritiqueOutput,
    CritiqueRequest,
    CritiqueResponse,
    MeasuredFindingItem,
    NextExerciseRecommendation,
    PedagogicalSummary,
    QualitativeObservationItem,
)
from src.prompts.rubrics import (
    ADVANCED_SYSTEM_PROMPT,
    BEGINNER_SYSTEM_PROMPT,
    build_critique_user_prompt,
)
from src.tools.validator import validate_critique_measurements

logger = logging.getLogger(__name__)


def get_cache_key(request: CritiqueRequest) -> str:
    """Generate a deterministic hash key for caching critique responses."""
    content = f"{request.student.student_id}_{request.student.level}_{request.geometry.avg_convergence_error_deg}_{request.geometry.k_requested}_{request.geometry.line_count}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_from_cache(cache_key: str, cache_dir: Path) -> CritiqueOutput | None:
    """Load cached critique from disk if exists."""
    cache_file = cache_dir / f"{cache_key}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return CritiqueOutput(**data)
        except (json.JSONDecodeError, OSError, ValueError):
            return None
    return None


def save_to_cache(cache_key: str, critique: CritiqueOutput, cache_dir: Path) -> None:
    """Save critique output to disk cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{cache_key}.json"
    cache_file.write_text(critique.model_dump_json(indent=2), encoding="utf-8")


def generate_fallback_critique(request: CritiqueRequest) -> CritiqueOutput:
    """Generate a high-quality pedagogical critique without live API calls (for testing & offline demo)."""
    student = request.student
    geom = request.geometry
    is_beginner = student.level.lower() == "beginner"

    # Measured findings strictly derived from OpenCV
    measured = [
        MeasuredFindingItem(
            metric_name="average_convergence_error",
            measured_value=geom.avg_convergence_error_deg,
            unit="degrees",
            pedagogical_context=(
                f"Your perspective lines have an average deviation of {geom.avg_convergence_error_deg:.1f}° "
                + ("which shows great intuitive grasp of the vanishing point!" if geom.avg_convergence_error_deg < 3.0 else "which gives room to align distant edges more precisely.")
            ),
        ),
    ]

    for vp in geom.vanishing_points:
        measured.append(
            MeasuredFindingItem(
                metric_name=f"{vp.label.lower()}_convergence_error",
                measured_value=vp.avg_error_deg,
                unit="degrees",
                pedagogical_context=f"The lines heading towards {vp.label} converge with an average error of {vp.avg_error_deg:.1f}° across {vp.supporting_lines} detected construction edges.",
            )
        )

    # Qualitative observations (Plane B: Line weight, spatial clarity, cleanliness)
    if is_beginner:
        qualitative = [
            QualitativeObservationItem(
                aspect="line_weight",
                observation="Great bold lines for the front face of the box! Try keeping your construction lines a bit lighter.",
                status="strength",
            ),
            QualitativeObservationItem(
                aspect="spatial_clarity",
                observation="The box has a nice 3D depth and feels solid on the table.",
                status="proficient",
            ),
        ]
        pedagogical = PedagogicalSummary(
            strengths=["Clear 3D box structure", "Good confidence in drawing straight edges"],
            focus_area="Keeping pencil pressure light when aiming towards the horizon dot.",
            encouragement=f"Fantastic work, {student.name}! Every box you draw makes your 3D vision stronger!",
        )
        next_ex = NextExerciseRecommendation(
            title="3 Floating Cubes in 1-Point Perspective",
            description="Draw three boxes: one below the horizon, one right at eye-level, and one floating high up.",
            target_metric="1-point convergence consistency",
            difficulty="beginner",
        )
        headline = f"Awesome 3D Box Practice, {student.name}!"
    else:
        qualitative = [
            QualitativeObservationItem(
                aspect="line_weight",
                observation="Good distinction between light construction guidelines and final contours. Reinforce the leading vertical edge for stronger visual hierarchy.",
                status="proficient",
            ),
            QualitativeObservationItem(
                aspect="spatial_clarity",
                observation="Clean volume definition with readable receding planes towards both vanishing points.",
                status="strength",
            ),
        ]
        pedagogical = PedagogicalSummary(
            strengths=["Consistent vanishing point convergence", "Solid vertical alignment on primary axes"],
            focus_area="Tightening convergence on secondary depth lines extending to F1.",
            encouragement=f"Very solid technical discipline, {student.name}. Your spatial reading is clean and ready for complex volumetric forms.",
        )
        next_ex = NextExerciseRecommendation(
            title="2-Point Perspective: Stepped Architectural Form",
            description="Construct a main box and carve out a stepped entrance, verifying all receding horizontal edges converge to F1 and F2.",
            target_metric="2-point convergence & dimensional consistency",
            difficulty="advanced",
        )
        headline = f"Perspective Analysis: Strong Volumetric Control, {student.name}"

    return CritiqueOutput(
        student_name=student.name,
        level=student.level,
        headline=headline,
        measured_findings=measured,
        qualitative_observations=qualitative,
        pedagogical_summary=pedagogical,
        next_exercise=next_ex,
        source="fallback",
        model_version="deterministic-template",
        validated=True,
    )


def call_vertex_ai_critique(
    request: CritiqueRequest,
    system_prompt: str,
    user_prompt: str,
) -> CritiqueOutput:
    """Invoke Gemini Flash via Google GenAI SDK / Vertex AI with structured output."""
    try:
        from google import genai
        from google.genai import types

        # Initialize Vertex AI client
        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project,
            location=settings.gemini_location,
        )

        # The drawing itself, when we have it. Plane B asks the model about line weight and
        # spatial clarity; without the image those observations were being written about a
        # drawing the model had never seen — hallucinations, inside the one project whose
        # headline claim is that it does not hallucinate. The field existed on the request all
        # along and was simply never read.
        contents: list = []
        if request.image_base64:
            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(request.image_base64),
                    mime_type="image/png",
                )
            )
        contents.append(user_prompt)

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=CritiqueLlmOutput,
                temperature=0.2,
            ),
        )

        if not response.text:
            raise ValueError("Empty response from Vertex AI Gemini model.")

        data = json.loads(response.text)
        # Provenance is stamped here, by the server, from what actually happened.
        return CritiqueOutput(
            **CritiqueLlmOutput(**data).model_dump(),
            source="vertex",
            model_version=settings.gemini_model,
        )

    except Exception as exc:  # noqa: BLE001 - see below
        # Deliberately broad: a missing credential, a quota error, a renamed model and a network
        # fault must all end in a usable critique rather than a 500 in front of a child.
        #
        # But it is **logged and labelled**. This used to be a bare `except` that returned the
        # template with `validated=True` and `model_version="gemini-3.5-flash"`, so deleting
        # Vertex AI from the project would have changed nothing anyone could observe. The caller,
        # the UI and the tests now get `source="fallback"` and this line lands in Cloud Logging.
        logger.warning(
            "Vertex AI critique failed (%s: %s); serving the deterministic studio template instead.",
            type(exc).__name__,
            exc,
        )
        return generate_fallback_critique(request)


def generate_pedagogical_critique(request: CritiqueRequest) -> CritiqueResponse:
    """Generate, validate, and cache a level-aware pedagogical critique (ADR-001 & PAT-001)."""
    cache_dir = Path(".cache/critiques")
    cache_key = get_cache_key(request)

    # 1. Check local cache if enabled
    if request.use_cache:
        cached_critique = load_from_cache(cache_key, cache_dir)
        if cached_critique is not None:
            return CritiqueResponse(critique=cached_critique, cached=True, validation_retries=0)

    # 2. Select Level-Aware System Prompt
    is_beginner = request.student.level.lower() == "beginner"
    system_prompt = BEGINNER_SYSTEM_PROMPT if is_beginner else ADVANCED_SYSTEM_PROMPT

    vps_desc = "\n".join(
        f"  - {vp.label}: {vp.point.x:.1f}, {vp.point.y:.1f} (Avg Error: {vp.avg_error_deg:.2f} deg, Supporting Lines: {vp.supporting_lines})"
        for vp in request.geometry.vanishing_points
    )
    if not vps_desc:
        vps_desc = "  - No clear vanishing points detected (low confidence)."

    user_prompt = build_critique_user_prompt(
        student_name=request.student.name,
        level=request.student.level,
        k_points=request.geometry.k_requested,
        avg_error_deg=request.geometry.avg_convergence_error_deg,
        max_error_deg=request.geometry.max_convergence_error_deg,
        line_count=request.geometry.line_count,
        confidence=request.geometry.confidence,
        vps_summary=vps_desc,
        student_intent=request.student_intent,
        student_difficulty=request.student_difficulty,
    )

    # 3. Call Vertex AI with anti-hallucination validation loop
    max_retries = 2
    retries_done = 0
    critique_result: CritiqueOutput | None = None

    for attempt in range(max_retries + 1):
        critique_result = call_vertex_ai_critique(request, system_prompt, user_prompt)
        is_valid, validation_errors = validate_critique_measurements(
            critique_result, request.geometry, had_image=bool(request.image_base64)
        )

        if is_valid:
            critique_result.validated = True
            break
        else:
            retries_done = attempt + 1
            # Add corrective feedback to user prompt for retry
            user_prompt += "\n\nPREVIOUS ATTEMPT FAILED VALIDATION:\n" + "\n".join(f"- {err}" for err in validation_errors)
            user_prompt += "\nPlease regenerate the critique using strictly and only the provided measured numbers."

    if critique_result is None or not critique_result.validated:
        # The model answered but could not satisfy the validator in three attempts. This branch
        # used to be silent — the same failure mode as the bare `except` above, and the reason a
        # request with no image produced a template with nobody able to say why.
        logger.warning(
            "Critique failed validation after %d retries (had_image=%s); serving the "
            "deterministic studio template instead. Last errors: %s",
            retries_done,
            bool(request.image_base64),
            "; ".join(validation_errors) if validation_errors else "none recorded",
        )
        critique_result = generate_fallback_critique(request)

    # 4. Save to cache
    save_to_cache(cache_key, critique_result, cache_dir)

    return CritiqueResponse(
        critique=critique_result,
        cached=False,
        validation_retries=retries_done,
    )
