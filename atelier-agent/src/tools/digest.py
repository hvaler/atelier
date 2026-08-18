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
_digests_store: dict[str, list[WeeklyDigest]] = {}


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
            weekly_avg_convergence_error_deg=0.0,
            error_reduction_deg=0.0,
            recurring_issues=[],
            weekly_summary=summary,
            recommended_focus=focus,
            next_week_practice_plan=plan,
        )
        _save_digest(digest)
        return digest

    # Calculate weekly metrics
    errors = [ex.geometry_analysis.avg_convergence_error_deg for ex in exercises]
    weekly_avg = float(np.mean(errors))

    # Error reduction calculation: compare first half to second half if >= 2 exercises
    if len(errors) >= 2:
        half = len(errors) // 2
        initial_avg = float(np.mean(errors[:half]))
        recent_avg = float(np.mean(errors[half:]))
        delta = round(initial_avg - recent_avg, 2)
    else:
        delta = 0.0

    derived_profile = memory_repo.derive_profile(student_id)
    recurring = derived_profile.recurring_issues

    # Synthesize weekly summary text
    if delta > 0.0:
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
        weekly_avg_convergence_error_deg=round(weekly_avg, 2),
        error_reduction_deg=delta,
        recurring_issues=recurring,
        weekly_summary=summary,
        recommended_focus=focus,
        next_week_practice_plan=plan,
    )
    _save_digest(digest)
    return digest


def _save_digest(digest: WeeklyDigest) -> None:
    """Store digest record in memory."""
    if digest.student_id not in _digests_store:
        _digests_store[digest.student_id] = []
    _digests_store[digest.student_id].append(digest)


def get_student_digests(student_id: str) -> list[WeeklyDigest]:
    """Retrieve all chronological weekly digests for a student."""
    return _digests_store.get(student_id, [])
