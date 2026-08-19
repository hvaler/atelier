"""Pydantic data models for pedagogical critique and student profiles (ADR-001 & ADR-005)."""

from typing import Literal

from pydantic import BaseModel, Field

from src.models.geometry import GeometryAnalysisResult


class StudentProfile(BaseModel):
    student_id: str = Field(..., description="Unique student identifier")
    name: str = Field(..., description="First name of the student (ADR-006)")
    level: str = Field("advanced", description="'beginner' (e.g. 9yo beginner) or 'advanced' (e.g. animation student)")
    tone_preference: str | None = Field("encouraging", description="Preferred pedagogical tone: 'encouraging', 'direct', 'technical'")
    recurring_issues: list[str] = Field(default_factory=list, description="Historical recurring difficulty areas")


class MeasuredFindingItem(BaseModel):
    metric_name: str = Field(..., description="Name of the deterministic metric from OpenCV (e.g. 'average_convergence_error', 'f1_error')")
    measured_value: float = Field(..., description="Exact numerical value measured by OpenCV")
    unit: str = Field("degrees", description="Measurement unit ('degrees', 'points', 'lines')")
    pedagogical_context: str = Field(..., description="Instructor explanation grounded strictly on this measured metric")


class QualitativeObservationItem(BaseModel):
    aspect: str = Field(..., description="Aspect assessed: 'line_weight', 'spatial_clarity', 'construction_cleanliness', 'volumetrics'")
    observation: str = Field(..., description="Qualitative feedback without inventing quantitative numbers")
    status: str = Field(..., description="'strength', 'needs_attention', or 'proficient'")


class PedagogicalSummary(BaseModel):
    strengths: list[str] = Field(..., description="1-3 specific drawing techniques done well")
    focus_area: str = Field(..., description="The ONE primary technical improvement to focus on next")
    encouragement: str = Field(..., description="Empathetic closing tailored to student's level and tone preference")


class NextExerciseRecommendation(BaseModel):
    title: str = Field(..., description="Recommended follow-up exercise title")
    description: str = Field(..., description="Step-by-step instructions for the practice exercise")
    target_metric: str = Field(..., description="Specific geometric or qualitative skill targeted")
    difficulty: str = Field("appropriate", description="'beginner', 'intermediate', or 'advanced'")


class CritiqueLlmOutput(BaseModel):
    """
    The critique as the model is allowed to produce it (ADR-001).

    This is the `response_schema` handed to Gemini, and it deliberately carries **no provenance
    fields**. When `model_version` was part of the schema the model filled it in itself, and the
    cached outputs prove what that costs: real Gemini responses came back claiming
    `"Atelier-v2.1-Pro"`, `"Atelier-v1"` and `"Atelier-v2"`, while the entries that read
    `"gemini-3.5-flash"` were the offline template. The field said the opposite of the truth.

    A system whose thesis is that the model may not assert a measurement must not let it assert
    which model produced the answer either. Provenance is set by the server in `CritiqueOutput`.
    """

    student_name: str
    level: str
    headline: str = Field(..., description="Engaging summary headline for the critique")
    measured_findings: list[MeasuredFindingItem] = Field(
        default_factory=list,
        description="Plane A (Quantitative): Grounded 100% strictly in OpenCV measurements",
    )
    qualitative_observations: list[QualitativeObservationItem] = Field(
        default_factory=list,
        description="Plane B (Qualitative): Studio instructor rubric observations (line weight, cleanliness, clarity)",
    )
    pedagogical_summary: PedagogicalSummary
    next_exercise: NextExerciseRecommendation


class CritiqueOutput(CritiqueLlmOutput):
    """A critique plus the provenance the server knows and the model does not."""

    source: Literal["vertex", "fallback"] = Field(
        "fallback",
        description=(
            "Where this critique came from. 'vertex' means Gemini answered; 'fallback' means the "
            "deterministic studio template did. Defaults to 'fallback' on purpose: unless "
            "something proves a model was involved, none was."
        ),
    )
    model_version: str = Field(
        "deterministic-template",
        description="Set by the server, never by the model. Names the template when source is 'fallback'.",
    )
    validated: bool = Field(False, description="Whether the critique passed all anti-hallucination validation gates")


class CritiqueRequest(BaseModel):
    image_base64: str | None = Field(None, description="Base64-encoded drawing image")
    geometry: GeometryAnalysisResult = Field(..., description="Deterministic measurements from OpenCV analyze_geometry")
    student: StudentProfile = Field(..., description="Student profile and learning level")
    student_intent: str | None = Field(None, description="What the student intended to practice (ASK step)")
    student_difficulty: str | None = Field(None, description="What part felt hardest during the drawing")
    language: Literal["en", "es"] = Field(
        "en",
        description=(
            "Language the critique prose must be written in. The measurements are the same "
            "either way; only the teaching changes language. A student reading feedback in a "
            "language they are still learning is being taught two things at once."
        ),
    )
    use_cache: bool = Field(True, description="Whether to check local demo cache before invoking LLM")


class CritiqueResponse(BaseModel):
    critique: CritiqueOutput
    cached: bool = Field(False, description="Whether the critique was served from local demo cache")
    validation_retries: int = Field(0, description="Number of validation retries executed to correct hallucinated numbers")
