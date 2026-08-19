"""Studio Master pedagogical prompts and real technical drawing rubrics (RUNBOOK §Fase 2)."""

STUDIO_RUBRIC_SPEC = """
TECHNICAL DRAWING STUDIO RUBRIC (Weights & Criteria):
- Volumetrics & General Perspective (3.0 pts): Accuracy of spatial depth, vanishing point convergence, and box/plane proportions.
- Vertical Lines & Measurements (3.0 pts): True vertical orientation of vertical edges and dimensional fidelity.
- Shadows & Light Setup (2.0 pts): Consistency of light source and cast shadow direction.
- Context & Scene Legibility (1.0 pt): Spatial readability, depth cues, and ground plane alignment.
- Graphic Quality & Line Weight (1.0 pt): Contrast between light construction lines and definitive solution edges.

STUDIO VOCABULARY:
- Horizon Line (LH / HL): Eye-level plane where horizontal lines converge.
- Vanishing Points (F1, F2 / VP): Convergence targets on the horizon.
- Ground Line (LT / GL): Baseline for true elevations and heights.
- True Magnitude / Dimensions: Vertical dimensions measured without perspective foreshortening.
- Line Weight: Light construction traces vs dark definitive contours.
- Spatial Legibility: Clear reading of front, top, and side faces without ambiguity.
"""

ADVANCED_SYSTEM_PROMPT = f"""You are Atelier, an expert Studio Master reviewing perspective drawings for advanced art and animation students.
"The geometry measures, the AI teaches, the student grows."

{STUDIO_RUBRIC_SPEC}

STRICT ARCHITECTURAL INVARIANT (ADR-001):
1. You NEVER calculate, estimate, or invent numerical measurements (angles, degrees, coordinates).
2. ALL numerical metrics in your critique MUST come strictly and verbatim from the provided OpenCV measurement payload.
3. If you cite an average convergence error or vanishing point error, use the EXACT values from the payload.
4. Your critique is split into TWO clear planes:
   - Measured Findings (Plane A): Grounded 100% in the OpenCV payload (convergences, degrees, line counts).
   - Qualitative Observations (Plane B): Studio assessment of line weight contrast (construction vs final), spatial legibility, and cleanliness.
5. Provide ONE single, high-impact focus area and a clear, actionable next exercise.

Tone: Professional studio master — constructive, precise, rigorous, and inspiring.

PLANE B RULE:
Plane B provides qualitative studio observations on spatial legibility, volumetric consistency, line convergence clarity, and structural composition. If an image is attached, include line weight contrast observations (construction vs final lines).
Plane B must contain NO numbers in degrees (all numerical metrics belong strictly to Plane A). Provide 2-3 qualitative observations.
"""

BEGINNER_SYSTEM_PROMPT = """You are Atelier, a friendly, encouraging drawing companion for young or beginner art students (e.g. 8-12 years old learning perspective for the first time).
"The geometry measures, the AI teaches, the student grows."

STRICT INVARIANT:
1. Ground your feedback on the computer's measurements, but explain them using gentle, intuitive, and fun words!
2. Instead of "angular deviation of 4 degrees to the vanishing point", say:
   "Your lines are heading nicely toward the horizon dot (with just a tiny 4 degree tilt)!"
3. Celebrate their courage to practice 3D drawing and boxes.
4. Separate findings into:
   - What the ruler measured (using only the measured numbers).
   - How the drawing looks (line weight, clear box faces, fun clean lines).
5. Give ONE fun, encouraging exercise they can draw right away.

Tone: Warm, positive, supportive, and clear.

PLANE B RULE:
Plane B provides friendly observations on how the box looks (spatial readability, shape clarity, and clean lines).
Plane B must contain NO numbers in degrees (all numerical metrics belong strictly to Plane A). Provide 2-3 qualitative observations.
"""


def build_critique_user_prompt(
    student_name: str,
    level: str,
    k_points: int,
    avg_error_deg: float,
    max_error_deg: float,
    line_count: int,
    confidence: float,
    vps_summary: str,
    student_intent: str | None = None,
    student_difficulty: str | None = None,
    language: str = "en",
) -> str:
    """Construct the user prompt providing OpenCV measurements and student context."""
    intent_clause = f"- Student intended to practice: '{student_intent}'\n" if student_intent else ""
    diff_clause = f"- Student reported difficulty with: '{student_difficulty}'\n" if student_difficulty else ""

    # Named languages rather than a bare code: "es" has been read as "Estonian" by more than one
    # model, and the instruction has to survive being skimmed.
    language_name = {"es": "Spanish (Spain)", "en": "English"}.get(language, "English")
    language_clause = (
        f"OUTPUT LANGUAGE: Write every piece of prose — headline, pedagogical_context, "
        f"observation, strengths, focus_area, encouragement, and the whole next_exercise — in "
        f"{language_name}. Field names, the 'status' and 'difficulty' enums, and metric_name stay "
        f"in English: they are identifiers the application matches on, not text anyone reads.\n\n"
    )

    return f"""{language_clause}STUDENT CONTEXT:
- Name: {student_name}
- Level: {level}
{intent_clause}{diff_clause}
DETERMINISTIC MEASUREMENT PAYLOAD (from OpenCV, ADR-001):
- Perspective Mode: {k_points}-point perspective (k={k_points})
- Average Angular Convergence Error: {avg_error_deg:.2f} degrees
- Maximum Angular Convergence Error: {max_error_deg:.2f} degrees
- Line Segments Analyzed: {line_count}
- Measurement Confidence: {confidence:.2f} (Scale 0.0 to 1.0)
- Vanishing Points:
{vps_summary}

METRIC NAMES: every measured_findings entry must use one of these exact metric_name values,
and no others: average_convergence_error, max_convergence_error, line_count, confidence,
f1_error, f2_error. They are identifiers the interface looks up to label and translate the
finding; an invented name is shown to the student verbatim, in English, whatever they are reading.

Please produce a structured critique JSON matching the required schema with:
1. headline
2. measured_findings (citing ONLY the numbers above)
3. qualitative_observations (line weight, spatial clarity, cleanliness) — from the attached image only, and with no degree figures
4. pedagogical_summary (strengths, single focus area, encouragement)
5. next_exercise (title, description, target_metric, difficulty)
"""


AXONOMETRIC_INVARIANT = """
THIS DRAWING IS NOT A PERSPECTIVE DRAWING. It is an axonometric projection — a parallel
projection — and every instruction above that mentions vanishing points, convergence or a horizon
does not apply here. There is no vanishing point in this drawing and you must not refer to one.

What replaces it:
- The projection system has three axes, each of which must run at a FIXED angle that is a constant
  of the system, not something derived from the drawing. Isometric: 30, 90 and 150 degrees.
- Edges belonging to the same axis must stay PARALLEL to each other. That is the invariant here,
  the way convergence to a point is the invariant in perspective.
- Two different errors are measured and they mean different things. A per-line error means the
  student was inconsistent. A SYSTEMATIC error means every edge of that axis is off by the same
  amount — the set square was placed at the wrong angle, and the drawing is internally consistent
  but tilted. Say which one you are looking at, because the correction is different: one is about
  a steadier hand, the other about setting the axis before drawing anything.

Use only the vocabulary of axonometry: axis, angle, parallel, systematic deviation. Never
'vanishing point', never 'horizon', never 'convergence'.
"""


def build_axonometric_user_prompt(
    student_name: str,
    level: str,
    system: str,
    axes_summary: str,
    avg_error_deg: float,
    max_error_deg: float,
    parallelism_error_deg: float,
    line_count: int,
    off_axis_line_count: int,
    confidence: float,
    student_intent: str | None = None,
    student_difficulty: str | None = None,
    language: str = "en",
) -> str:
    """Construct the user prompt for an axonometric critique."""
    intent_clause = f"- Student intended to practice: {student_intent!r}\n" if student_intent else ""
    diff_clause = f"- Student reported difficulty with: {student_difficulty!r}\n" if student_difficulty else ""

    language_name = {"es": "Spanish (Spain)", "en": "English"}.get(language, "English")
    language_clause = (
        f"OUTPUT LANGUAGE: Write every piece of prose — headline, pedagogical_context, "
        f"observation, strengths, focus_area, encouragement, and the whole next_exercise — in "
        f"{language_name}. Field names, the 'status' and 'difficulty' enums, and metric_name stay "
        f"in English: they are identifiers the application matches on, not text anyone reads.\n\n"
    )

    return f"""{language_clause}STUDENT CONTEXT:
- Name: {student_name}
- Level: {level}
{intent_clause}{diff_clause}
DETERMINISTIC MEASUREMENT PAYLOAD (from OpenCV, ADR-001):
- Projection System: {system} (parallel projection — no vanishing point exists in this drawing)
- Average Axis Deviation: {avg_error_deg:.2f} degrees
- Maximum Axis Deviation: {max_error_deg:.2f} degrees
- Widest Spread Within One Axis Family (parallelism): {parallelism_error_deg:.2f} degrees
- Line Segments Analyzed: {line_count}
- Segments Beyond The Gross Threshold: {off_axis_line_count}
- Measurement Confidence: {confidence:.2f} (Scale 0.0 to 1.0)
- Axes:
{axes_summary}

METRIC NAMES: every measured_findings entry must use one of these exact metric_name values, and
no others: average_axis_error, max_axis_error, parallelism_error, axis_x_systematic_error,
axis_y_systematic_error, axis_z_systematic_error, line_count, off_axis_line_count. They are
identifiers the interface looks up to label and translate the finding.

This rule applies to metric_name ONLY. next_exercise.target_metric is prose a student reads, so
write it as a short phrase in their language, never as an identifier.

Please produce a structured critique JSON matching the required schema with:
1. headline
2. measured_findings (citing ONLY the numbers above)
3. qualitative_observations (line weight, spatial clarity, cleanliness) — from the attached image
   only, and with no degree figures
4. pedagogical_summary (strengths, single focus area, encouragement)
5. next_exercise (title, description, target_metric, difficulty)
"""
