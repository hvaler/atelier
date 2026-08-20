"""Weekly digest generator and practice planner orchestrated via Cloud Scheduler (ADR-004)."""

import uuid
from datetime import UTC, datetime

import numpy as np

from src.models.digest import PracticePlanDay, WeeklyDigest
from src.tools.memory import memory_repo


def get_current_iso_week() -> str:
    """Return current ISO week string, e.g. '2026-W34'."""
    now = datetime.now(UTC)
    return f"{now.isocalendar().year}-W{now.isocalendar().week:02d}"


# In-memory store for digests: student_id -> list of WeeklyDigest


def generate_weekly_digest(student_id: str, week_id: str | None = None) -> WeeklyDigest:
    """Aggregate a student's weekly drawing sessions, compute error delta, and synthesize practice plan."""
    student = memory_repo.get_student(student_id)
    if not student:
        raise ValueError(f"Student '{student_id}' not found.")

    target_week = week_id or get_current_iso_week()
    exercises = memory_repo.get_student_exercises(student_id)
    is_beginner = student.level == "beginner"

    if not exercises:
        # Default placeholder digest if student has no exercises yet
        if is_beginner:
            plan = [
                PracticePlanDay(
                    day="Monday",
                    title="First 3D Box on Table",
                    description="Draw a single cube below the horizon line with light pencil pressure.",
                    target_metric="1-point convergence consistency",
                ),
                PracticePlanDay(
                    day="Wednesday",
                    title="Floating Cube Practice",
                    description="Draw a box floating above eye-level.",
                    target_metric="Horizon alignment",
                ),
                PracticePlanDay(
                    day="Friday",
                    title="Two Boxes in Space",
                    description="Draw two boxes: one near and one far.",
                    target_metric="Spatial depth & line weight",
                ),
            ]
            summary = f"Welcome to your first week at Atelier, {student.name}! Let's start with simple 3D box foundations."
            focus = "Frontal face alignment and light construction traces."
        else:
            plan = [
                PracticePlanDay(
                    day="Monday",
                    title="2-Point Perspective Calibration Drill",
                    description="Construct 3 cubes with F1 and F2 spaced at least 3x the object width.",
                    target_metric="F1 / F2 convergence error < 2.0°",
                ),
                PracticePlanDay(
                    day="Wednesday",
                    title="Intersecting Prisms & Volumetric Cuts",
                    description="Carve a cylindrical or rectangular void through a solid rectangular prism.",
                    target_metric="Spatial legibility & true magnitude on LT",
                ),
                PracticePlanDay(
                    day="Friday",
                    title="Architectural Elevation in Oblique Perspective",
                    description="Construct a multi-story building volume with consistent window module recessions.",
                    target_metric="Dimensional fidelity & line weight contrast",
                ),
            ]
            summary = f"Welcome to Atelier Studio, {student.name}. Ready to calibrate your 2-point perspective and volumetric precision."
            focus = "2-Point convergence and line weight contrast."

        digest = WeeklyDigest(
            digest_id=f"digest-{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            student_name=student.name,
            week_id=target_week,
            total_drawings=0,
            weekly_avg_convergence_error_deg=None,
            error_reduction_deg=None,
            recurring_issues=[],
            weekly_summary=summary,
            recommended_focus=focus,
            next_week_practice_plan=plan,
        )
        _save_digest(digest)
        return digest

    # Only conic exercises carry a convergence error. `geometry_analysis` is None for
    # axonometric and orthographic records, deliberately — an axis deviation and a convergence
    # error are both degrees and are not the same quantity. This line used to read the field off
    # every exercise, so one parallel-projection drawing in the week raised AttributeError and the
    # digest returned 500. Being a Cloud Scheduler job, it did so with nobody watching.
    errors = [
        ex.geometry_analysis.avg_convergence_error_deg
        for ex in exercises
        if ex.geometry_analysis is not None
    ]
    weekly_avg = float(np.mean(errors)) if errors else None

    # Error reduction: first half against second half, and only when there are two halves to
    # compare. None rather than 0.0, because 0.0 is a real reading meaning "no change".
    if len(errors) >= 2:
        half = len(errors) // 2
        initial_avg = float(np.mean(errors[:half]))
        recent_avg = float(np.mean(errors[half:]))
        delta = round(initial_avg - recent_avg, 2)
    else:
        delta = None

    derived_profile = memory_repo.derive_profile(student_id)
    recurring = derived_profile.recurring_issues

    # Synthesize weekly summary text. Every branch below has to survive a week with no conic
    # drawing in it, which is what the digest used to crash on.
    if weekly_avg is None:
        improvement_phrase = (
            "No conic exercise this week, so there is no convergence average to report. The "
            "parallel-projection work is recorded and critiqued — it is measured against a "
            "different reference, and averaging the two would describe neither."
        )
    elif delta is None:
        improvement_phrase = f"One conic drawing this week, at {weekly_avg:.1f}° average error."
    elif delta > 0.0:
        improvement_phrase = f"Your average convergence error decreased by {delta:.1f}°, showing notable consistency!"
    elif delta < 0.0:
        improvement_phrase = "You tackled more complex oblique angles this week — errors are expected when stepping up difficulty!"
    else:
        improvement_phrase = f"Solid steady performance with an average error of {weekly_avg:.1f}°."

    if is_beginner:
        summary = f"Super job this week, {student.name}! You completed {len(exercises)} drawing practices. {improvement_phrase}"
        focus = "Keeping construction lines light while aiming at the horizon dot."
        plan = [
            PracticePlanDay(
                day="Monday",
                title="3 Aligned Cubes",
                description="Draw three boxes aligned side by side, aiming strictly to the center vanishing point.",
                target_metric="1-point convergence (< 3.0°)",
            ),
            PracticePlanDay(
                day="Wednesday",
                title="Tall Tower Box",
                description="Draw an elongated vertical box that crosses the horizon line.",
                target_metric="Vertical edge true alignment",
            ),
            PracticePlanDay(
                day="Friday",
                title="Stepped Block & Stairs",
                description="Draw a box and slice out a stair step on the side.",
                target_metric="Plane readability & line weight",
            ),
        ]
    else:
        summary = f"Weekly perspective review for {student.name}: {len(exercises)} drawing sessions analyzed. {improvement_phrase}"
        focus = recurring[0] if recurring else "Refining secondary convergence lines towards F1 and line weight hierarchy."
        plan = [
            PracticePlanDay(
                day="Monday",
                title="2-Point Perspective Calibration Drill",
                description="Construct 3 cubes with F1 and F2 spaced at least 3x the object width to prevent optical distortion.",
                target_metric="F1 / F2 convergence error < 2.0°",
            ),
            PracticePlanDay(
                day="Wednesday",
                title="Intersecting Prisms & Volumetric Cuts",
                description="Carve a cylindrical or rectangular void through a solid rectangular prism.",
                target_metric="Spatial legibility & true magnitude on LT",
            ),
            PracticePlanDay(
                day="Friday",
                title="Architectural Elevation in Oblique Perspective",
                description="Construct a multi-story building volume with consistent window module recessions.",
                target_metric="Dimensional fidelity & line weight contrast",
            ),
        ]

    digest = WeeklyDigest(
        digest_id=f"digest-{uuid.uuid4().hex[:8]}",
        student_id=student_id,
        student_name=student.name,
        week_id=target_week,
        total_drawings=len(exercises),
        weekly_avg_convergence_error_deg=round(weekly_avg, 2) if weekly_avg is not None else None,
        error_reduction_deg=delta,
        recurring_issues=recurring,
        weekly_summary=summary,
        recommended_focus=focus,
        next_week_practice_plan=plan,
    )
    _save_digest(digest)
    return digest


def _save_digest(digest: WeeklyDigest) -> None:
    """Store the digest wherever student memory lives."""
    memory_repo.save_digest(digest)


def get_student_digests(student_id: str) -> list[WeeklyDigest]:
    """Retrieve all chronological weekly digests for a student."""
    return memory_repo.get_digests(student_id)
