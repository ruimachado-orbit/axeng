#!/usr/bin/env python3
"""
Steering Report — Portfolio Aggregator
Assembles per-project data from Linear, GitHub Issues, Granola, and risk signals,
scores each project, and renders the weekly executive document.

Entry point:  generate_steering_report(week_ending: date | None) -> SteeringReport
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get as cfg_get
from project_map import build_maps, all_repos, owner_of_project, repos_for_project
from tools.linear_tool import linear_project_health
from tools.sprint_health import (
    predict_sprint_completion, calculate_sprint_metrics,
    sprint_health, sprint_velocity,
)
from tools.vacations import who_is_ooo_today
from tools.github_issues import enrich_with_issue_signals
from tools.github_activity import github_commits_summary
from tools.steering_granola import enrich_with_granola
from tools.steering_render import render_html, render_markdown
from tools.steering_schema import (
    CommitSignals,
    SprintSignals,
    CapacitySignals,
    Confidence,
    Evidence,
    EtaRisk,
    Forecast,
    IssueSignals,
    LinearSignals,
    PortfolioSummary,
    ProjectCard,
    Status,
    SteeringReport,
    TimelinePosition,
    TranscriptSignal,
    report_to_dict,
)


# ── Week boundaries ──────────────────────────────────────────────────────────

def _week_boundaries(week_ending: date | None = None) -> tuple[date, date]:
    """Return (week_start Monday, week_end Friday) for the report period."""
    end = week_ending or date.today()
    # Snap to the most recent Friday
    days_since_friday = (end.weekday() - 4) % 7
    friday = end - timedelta(days=days_since_friday)
    monday = friday - timedelta(days=4)
    return monday, friday


# ── Timeline calculations ────────────────────────────────────────────────────

def _timeline_metrics(start_date_str: str | None, target_date_str: str | None) -> dict:
    """
    Compute time_progress_pct, work_progress_pct placeholder, days_left,
    timeline_position, eta_risk from project dates.
    Returns a dict of computed fields (work_progress filled later from Linear).
    """
    today = date.today()
    result: dict[str, Any] = {
        "days_left": None,
        "time_progress_pct": 0.0,
        "timeline_position": "on_plan",
        "eta_risk": "low",
    }

    if not target_date_str:
        return result

    try:
        target = date.fromisoformat(target_date_str[:10])
        result["days_left"] = (target - today).days

        if start_date_str:
            start = date.fromisoformat(start_date_str[:10])
            total_days = (target - start).days
            elapsed = (today - start).days
            if total_days > 0:
                result["time_progress_pct"] = round(min(elapsed / total_days * 100, 100), 1)
        else:
            # No start date — estimate from 90-day window
            assumed_start = target - timedelta(days=90)
            total_days = 90
            elapsed = (today - assumed_start).days
            result["time_progress_pct"] = round(min(max(elapsed / total_days * 100, 0), 100), 1)

    except (ValueError, TypeError):
        pass

    return result


def _compute_timeline_position(time_pct: float, work_pct: float) -> TimelinePosition:
    gap = work_pct - time_pct
    if gap >= 5:
        return "ahead"
    if gap >= -10:
        return "on_plan"
    if gap >= -25:
        return "behind"
    return "significantly_behind"


def _compute_eta_risk(days_left: int | None, timeline_position: TimelinePosition) -> EtaRisk:
    if days_left is not None and days_left < 0:
        return "critical"
    if timeline_position == "significantly_behind":
        return "high" if (days_left or 99) > 14 else "critical"
    if timeline_position == "behind":
        return "medium"
    if timeline_position == "ahead":
        return "low"
    return "low"


# ── Linear → LinearSignals ───────────────────────────────────────────────────

def _extract_linear_signals(project_data: dict) -> LinearSignals:
    metrics = project_data.get("metrics", {})
    return LinearSignals(
        completion_rate=metrics.get("completion_rate", 0.0),
        staleness_rate=metrics.get("staleness_rate", 0.0),
        velocity=metrics.get("velocity", 0.0),
        in_progress=metrics.get("in_progress", 0),
        todo=metrics.get("todo", 0),
        completed=metrics.get("completed", 0),
        top_stale_issues=project_data.get("top_stale_issues", []),
        risks=project_data.get("risks", []),
    )


# ── Scoring (Phase 4 extends this) ──────────────────────────────────────────

def _score_project(
    linear: LinearSignals,
    issues: IssueSignals,
    time_pct: float,
    work_pct: float,
    transcript_signals: list[TranscriptSignal],
    velocity_trend: str = "stable",
) -> tuple[float, Confidence, Status, Forecast]:
    """
    Weighted score using raw signals (not the derived Linear health score).
    Weights: Linear delivery 35% | timeline alignment 25% | issue risk 20% |
             transcript 15% | staleness penalty 5%
    velocity_trend is a team-wide modifier: declining nudges score down,
    improving nudges it up — labelled in evidence so it's not misread as
    project-specific.
    Returns (health_score, confidence, status, forecast).
    """
    # Linear delivery component — raw completion + velocity
    linear_score = (
        linear.completion_rate * 0.6 +
        min(linear.velocity * 20, 40)  # cap velocity contribution
    )

    # Timeline alignment — work ahead/behind calendar
    gap = work_pct - time_pct          # positive = ahead, negative = behind
    if gap >= 0:
        timeline_score = 100.0
    elif gap >= -15:
        timeline_score = 100 + gap * 3   # gradual penalty
    else:
        timeline_score = max(0, 100 + gap * 5)

    # Issue risk — inverted (high risk = low score)
    issue_score = max(0, 100 - issues.risk_score)

    # Staleness penalty
    staleness_score = max(0, 100 - linear.staleness_rate)

    # Weighted total
    health_score = (
        linear_score * 0.35 +
        timeline_score * 0.25 +
        issue_score * 0.20 +
        staleness_score * 0.05
    )

    # Velocity trend modifier (team-wide signal — applied before capping)
    if velocity_trend == "declining":
        health_score = max(0, health_score - 8)
    elif velocity_trend == "improving":
        health_score = min(100, health_score + 5)

    # Transcript modifier — urgent tone caps status at at_risk regardless of score
    urgent_transcript = any(
        ts.confidence_tone == "urgent" for ts in transcript_signals
    )
    has_transcript_blockers = any(
        ts.blockers for ts in transcript_signals
    )
    if urgent_transcript:
        health_score = min(health_score, 59)

    health_score = round(min(max(health_score, 0), 100), 1)

    # Status thresholds
    if health_score >= 75 and not urgent_transcript:
        status: Status = "on_track"
    elif health_score >= 50:
        status = "at_risk"
    else:
        status = "off_track"

    # Confidence band
    if health_score >= 75 and not urgent_transcript and not has_transcript_blockers:
        confidence: Confidence = "high"
    elif health_score >= 50:
        confidence = "medium"
    else:
        confidence = "low"

    # Forecast
    if status == "on_track":
        forecast: Forecast = "delivering_as_planned"
    elif issues.unowned_count > 3 or linear.staleness_rate > 60:
        forecast = "unowned_assign_now"
    elif urgent_transcript or issues.blocked_threads > 0:
        forecast = "blocked_needs_escalation"
    else:
        forecast = "target_date_at_risk"

    return health_score, confidence, status, forecast


# ── Decision detection ───────────────────────────────────────────────────────

def _build_week_delta(card: ProjectCard) -> str | None:
    """
    Synthesise a one-sentence week summary from Linear issues closed,
    GitHub Issues backlog movement, and commits. Replaces raw signal lists.
    """
    parts = []

    # Issues closed vs opened (Linear completion rate is cumulative so use
    # GitHub Issues backlog_growth as the week-scoped signal)
    lin = card.linear_signals
    iss = card.issue_signals
    cs = card.commit_signals

    # Completed issues this period from Linear velocity
    if lin.completed > 0 and lin.velocity > 0:
        closed_est = max(1, round(lin.velocity * 7))  # estimated from velocity
        parts.append(f"{closed_est} issue{'s' if closed_est > 1 else ''} completed")

    # Backlog movement
    bg = iss.backlog_growth
    if bg > 2:
        parts.append(f"+{bg} net new issues (backlog growing)")
    elif bg < -1:
        parts.append(f"{abs(bg)} more closed than opened")

    # Commits
    if cs.commits_this_week > 0:
        parts.append(f"{cs.commits_this_week} commit{'s' if cs.commits_this_week > 1 else ''}")

    # Silent repo warning
    if cs.quiet_repos and card.repos:
        parts.append(f"{len(cs.quiet_repos)} repo silent")

    return " · ".join(parts) if parts else None


def _build_next_week(card: ProjectCard) -> str | None:
    """
    Synthesise what's planned/committed for next week from:
    - Commitments extracted from Granola meeting notes
    - Linear in-progress + high-priority todo issues
    - Upcoming milestones
    """
    parts: list[str] = []

    # 1. Meeting commitments (highest signal — explicitly said on a call)
    for ts in card.transcript_signals:
        for commitment in ts.commitments[:2]:
            if commitment:
                parts.append(f'"{commitment}" (committed in {ts.title})')
        if len(parts) >= 2:
            break

    # 2. Upcoming milestone
    if card.milestones and not parts:
        from datetime import date as _d, timedelta
        today = _d.today()
        next_2w = today + timedelta(days=14)
        soon = [
            m for m in card.milestones
            if m.get("target_date") and today.isoformat() <= m["target_date"] <= next_2w.isoformat()
        ]
        soon.sort(key=lambda m: m["target_date"])
        if soon:
            m = soon[0]
            parts.append(f"Milestone due: {m['name']} ({m['target_date']})")

    # 3. Linear in-progress work as a signal of what's being pushed
    lin = card.linear_signals
    if not parts and lin.in_progress > 0:
        parts.append(
            f"{lin.in_progress} issue{'s' if lin.in_progress > 1 else ''} in progress"
            + (f", {lin.todo} queued" if lin.todo > 0 else "")
        )

    return " · ".join(parts) if parts else None


def _current_milestone(card: ProjectCard) -> dict | None:
    """Return the active milestone: the earliest upcoming one, or the last passed one."""
    from datetime import date as _d
    today = _d.today().isoformat()
    if not card.milestones:
        return None
    sorted_ms = sorted(card.milestones, key=lambda m: m.get("target_date", ""))
    upcoming = [m for m in sorted_ms if m.get("target_date", "") >= today]
    if upcoming:
        return upcoming[0]
    # All milestones passed — return the last one
    return sorted_ms[-1] if sorted_ms else None


def _build_status_explanation(card: ProjectCard) -> list[str]:
    """
    Build a list of specific, evidence-based reasons why a project is at risk
    or off track. Mirrors the logic from sprint_health.predict_sprint_completion.
    """
    reasons: list[str] = []
    lin = card.linear_signals
    work = card.work_progress_pct
    time = card.time_progress_pct
    gap = work - time  # negative = behind schedule

    # Timeline position
    if card.days_left is not None and card.days_left < 0:
        reasons.append(f"Target date passed {abs(card.days_left)}d ago — {int(work)}% complete")
    elif gap < -20:
        reasons.append(
            f"{int(time)}% of time elapsed but only {int(work)}% done "
            f"— {int(abs(gap))}% behind schedule"
        )
    elif gap < -10:
        reasons.append(f"Slightly behind: {int(work)}% done vs {int(time)}% time elapsed")

    # Velocity vs needed
    if card.days_left and card.days_left > 0 and lin.velocity > 0:
        remaining_issues = lin.todo + lin.in_progress
        needed_velocity = remaining_issues / card.days_left if card.days_left > 0 else 0
        if needed_velocity > lin.velocity * 1.5:
            reasons.append(
                f"Needs {needed_velocity:.2f} issues/day to finish on time "
                f"but current velocity is {lin.velocity:.2f}/day"
            )
    elif lin.velocity == 0 and (lin.todo + lin.in_progress) > 0:
        reasons.append(f"No velocity — {lin.todo + lin.in_progress} issues unstarted or stalled")

    # Staleness
    if lin.staleness_rate > 60:
        reasons.append(
            f"{int(lin.staleness_rate)}% of open issues not updated in 7+ days"
            + (f": {lin.top_stale_issues[0]}" if lin.top_stale_issues else "")
        )

    # Current milestone context
    ms = _current_milestone(card)
    if ms:
        from datetime import date as _d
        today = _d.today().isoformat()
        if ms["target_date"] < today:
            reasons.append(f"Milestone overdue: '{ms['name']}' was due {ms['target_date']}")

    return reasons


def _detect_decision(card: ProjectCard) -> str | None:
    """Return a one-line decision prompt if the project needs one, else None."""
    if card.forecast == "blocked_needs_escalation":
        blocker = card.blockers[0] if card.blockers else "blocker"
        return f"Unblock {card.name}: {blocker}"
    # Only fire unowned_assign_now if there are actually unowned issues
    if card.forecast == "unowned_assign_now" and card.issue_signals.unowned_count > 0:
        return f"Assign owner for {card.name} — {card.issue_signals.unowned_count} unowned issues"
    if card.forecast == "target_date_at_risk" and (card.days_left or 99) < 21:
        return f"Decide: rescope {card.name} or accept date slip ({card.days_left}d left)"
    if card.eta_risk in ("high", "critical") and card.status != "on_track":
        return f"Review {card.name} timeline — {card.eta_risk} ETA risk"
    return None


# ── Bottom line synthesis ────────────────────────────────────────────────────

def _build_bottom_line(projects: list[ProjectCard], decisions: list[dict]) -> str:
    n_decisions = len(decisions)
    off_track = [p for p in projects if p.status == "off_track"]
    at_risk = [p for p in projects if p.status == "at_risk"]
    on_track = [p for p in projects if p.status == "on_track"]

    if n_decisions == 0 and not off_track:
        return f"All {len(on_track)} projects are on track. No decisions required this week."

    parts = []
    if n_decisions:
        items = " and ".join(d["project"] for d in decisions[:2])
        suffix = f" (+{n_decisions - 2} more)" if n_decisions > 2 else ""
        parts.append(f"{n_decisions} decision{'s' if n_decisions > 1 else ''} needed — {items}{suffix}.")
    if off_track:
        names = ", ".join(p.name for p in off_track[:2])
        parts.append(f"{names} {'are' if len(off_track) > 1 else 'is'} off track.")
    if at_risk and not off_track:
        names = ", ".join(p.name for p in at_risk[:2])
        parts.append(f"{names} {'are' if len(at_risk) > 1 else 'is'} at risk.")
    if on_track:
        parts.append(f"{len(on_track)} project{'s' if len(on_track) > 1 else ''} on track.")

    return " ".join(parts)


# ── Capacity signals ─────────────────────────────────────────────────────────

def _collect_capacity() -> CapacitySignals:
    try:
        ooo = who_is_ooo_today()
        people = [v.get("person", "") for v in ooo.get("vacations", [])]
        return CapacitySignals(ooo_this_week=people)
    except Exception:
        return CapacitySignals()


# ── Main assembler ───────────────────────────────────────────────────────────

def generate_steering_report(week_ending: date | None = None) -> SteeringReport:
    """
    Assemble the full weekly steering report.
    Non-fatal errors per source are recorded in report.errors — never abort.
    """
    week_start, week_end = _week_boundaries(week_ending)
    report_id = f"steering-{week_end.isoformat()}"
    sources: list[str] = []
    errors: list[str] = []

    print("🏗  Building steering report...", file=sys.stderr)

    # ── 1. Project map ──────────────────────────────────────────────────────
    try:
        linear_github_map, _ = build_maps()
    except Exception as e:
        errors.append(f"project_map: {e}")
        linear_github_map = {}

    # ── 2. Linear project health ────────────────────────────────────────────
    print("  📋 Fetching Linear project health...", file=sys.stderr)
    linear_projects: list[dict] = []
    try:
        health_result = linear_project_health(days=7)
        linear_projects = health_result.get("projects", [])
        sources.append("linear")
    except Exception as e:
        errors.append(f"linear_project_health: {e}")

    # ── 3. Sprint signals (team-wide — cadence differs from weekly steering) ─
    print("  🏃 Fetching sprint signals...", file=sys.stderr)
    sprint_signals = SprintSignals()
    try:
        sh = sprint_health()
        vel = sprint_velocity(cycles=5)

        cycle = sh.get("cycle", {})
        metrics = sh.get("metrics", {})
        prediction = sh.get("prediction", {})

        # Days remaining in the active sprint
        days_remaining: int | None = None
        sprint_ends_at = cycle.get("ends_at") or cycle.get("endsAt")
        if sprint_ends_at:
            try:
                ends = datetime.fromisoformat(sprint_ends_at.replace("Z", "+00:00"))
                days_remaining = max(0, (ends.replace(tzinfo=None) - datetime.now()).days)
            except (ValueError, TypeError):
                pass

        sprint_signals = SprintSignals(
            sprint_name=cycle.get("name"),
            sprint_ends_at=sprint_ends_at,
            days_remaining_in_sprint=days_remaining,
            sprint_completion_rate=round(metrics.get("completion_rate", 0.0), 1),
            sprint_time_progress=round(prediction.get("time_progress", 0.0), 1),
            sprint_status=prediction.get("status", "unknown"),
            velocity_trend=vel.get("trend", "stable"),
            velocity_avg=round(vel.get("average_velocity", 0.0), 2),
            velocity_current=round(metrics.get("velocity", 0.0), 2),
            cycles_analyzed=vel.get("cycles_analyzed", 0),
        )
        sources.append("sprint")
    except Exception as e:
        errors.append(f"sprint_signals: {e}")

    # Build index by name for fast lookup
    linear_by_name = {p["name"]: p for p in linear_projects}

    # ── 3. Build project cards ──────────────────────────────────────────────
    print("  🃏 Building project cards...", file=sys.stderr)
    project_cards: list[ProjectCard] = []

    # Union of mapped projects + any Linear projects not yet in the map.
    # Mapped projects come first (they have repo/owner metadata); unmapped are
    # appended so they still appear in the report with a warning in evidence.
    mapped_names = set(linear_github_map.keys())
    unmapped_names = [p["name"] for p in linear_projects if p["name"] not in mapped_names]
    configured_projects = list(linear_github_map.keys()) + unmapped_names

    for proj_name in configured_projects:
        map_entry = linear_github_map.get(proj_name, {})
        lin_data = linear_by_name.get(proj_name, {})

        # Dates from Linear
        target_date = lin_data.get("target_date")
        start_date = lin_data.get("start_date")   # may be absent — patched in Phase 1 note

        # Timeline
        tl = _timeline_metrics(start_date, target_date)
        linear_signals = _extract_linear_signals(lin_data)
        work_pct = linear_signals.completion_rate
        time_pct = tl["time_progress_pct"]

        tl["timeline_position"] = _compute_timeline_position(time_pct, work_pct)
        tl["eta_risk"] = _compute_eta_risk(tl["days_left"], tl["timeline_position"])

        # Score (issue signals + transcript filled in later phases)
        dummy_issues = IssueSignals()
        health_score, confidence, status, forecast = _score_project(
            linear_signals, dummy_issues, time_pct, work_pct, []
        )

        # Blockers from linear risks + stale issues
        blockers: list[str] = list(linear_signals.risks)
        if linear_signals.top_stale_issues:
            blockers.append(
                f"{len(linear_signals.top_stale_issues)} stale issues: "
                + ", ".join(linear_signals.top_stale_issues[:2])
            )

        # Evidence
        evidence: list[Evidence] = []
        for risk in linear_signals.risks:
            evidence.append(Evidence(source="linear", text=risk, severity="warning"))
        if not lin_data:
            evidence.append(Evidence(
                source="linear",
                text=f"No Linear data found for project '{proj_name}'",
                severity="warning",
            ))

        card = ProjectCard(
            name=proj_name,
            owner=map_entry.get("owner", lin_data.get("lead", "Unassigned")),
            linear_project_id=lin_data.get("id"),
            repos=map_entry.get("repos", []),
            status=status,
            health_score=health_score,
            confidence=confidence,
            forecast=forecast,
            target_date=target_date,
            start_date=start_date,
            days_left=tl["days_left"],
            milestones=lin_data.get("milestones", []),
            time_progress_pct=time_pct,
            work_progress_pct=work_pct,
            timeline_position=tl["timeline_position"],
            eta_risk=tl["eta_risk"],
            linear_signals=linear_signals,
            issue_signals=dummy_issues,
            blockers=blockers,
            evidence=evidence,
        )
        project_cards.append(card)

    # ── 4. Attach velocity context to project cards ─────────────────────────
    # sprint_velocity is team-wide — labelled clearly so nobody read it
    # as project-specific. A declining trend compounds any per-project risk.
    if sprint_signals.velocity_trend == "declining":
        for card in project_cards:
            if not card.week_delta:
                card.week_delta = (
                    f"Team velocity declining "
                    f"(avg {sprint_signals.velocity_avg:.1f} pts/day, "
                    f"last {sprint_signals.cycles_analyzed} sprints)"
                )
            card.evidence.append(Evidence(
                source="sprint",
                text=f"Team velocity trend: declining (avg {sprint_signals.velocity_avg:.1f} pts/day)",
                severity="warning",
            ))
    elif sprint_signals.velocity_trend == "improving":
        for card in project_cards:
            card.evidence.append(Evidence(
                source="sprint",
                text=f"Team velocity trend: improving (avg {sprint_signals.velocity_avg:.1f} pts/day)",
                severity="info",
            ))

    # ── 6. Commit signals ───────────────────────────────────────────────────
    print("  📦 Fetching commit signals...", file=sys.stderr)
    try:
        commits_data = github_commits_summary(days=7)
        by_repo: dict[str, int] = {
            repo: info.get("count", 0)
            for repo, info in commits_data.get("by_repo", {}).items()
        }
        for card in project_cards:
            if not card.repos:
                continue
            active = [r for r in card.repos if by_repo.get(r, 0) > 0]
            quiet = [r for r in card.repos if by_repo.get(r, 0) == 0]
            total = sum(by_repo.get(r, 0) for r in card.repos)
            card.commit_signals = CommitSignals(
                commits_this_week=total,
                active_repos=active,
                quiet_repos=quiet,
            )
            if not total and card.repos:
                card.evidence.append(Evidence(
                    source="github_issues",
                    text=f"No commits in {len(card.repos)} repo(s) this week",
                    severity="warning",
                ))
        sources.append("github_commits")
    except Exception as e:
        errors.append(f"github_commits: {e}")

    # ── 7. GitHub Issues enrichment ─────────────────────────────────────────
    try:
        project_cards = enrich_with_issue_signals(project_cards, week_start.isoformat())
        sources.append("github_issues")
    except Exception as e:
        errors.append(f"github_issues: {e}")

    # ── 7. Granola transcript enrichment ────────────────────────────────────
    cross_project_signals: list[dict] = []
    try:
        project_cards, cross_project_signals = enrich_with_granola(
            project_cards, week_start.isoformat(), week_end.isoformat()
        )
        sources.append("granola")
    except Exception as e:
        errors.append(f"granola: {e}")

    # ── 8. Re-score with all signals now populated ───────────────────────────
    print("  🧮 Scoring projects...", file=sys.stderr)
    for card in project_cards:
        health_score, confidence, status, forecast = _score_project(
            card.linear_signals,
            card.issue_signals,
            card.time_progress_pct,
            card.work_progress_pct,
            card.transcript_signals,
            velocity_trend=sprint_signals.velocity_trend,
        )
        card.health_score = health_score
        card.confidence = confidence
        card.status = status
        card.forecast = forecast
        # Re-derive eta_risk now that issue signals are included
        card.eta_risk = _compute_eta_risk(card.days_left, card.timeline_position)

    # Build synthesised week summary + next week forecast + status explanation
    for card in project_cards:
        card.week_delta = _build_week_delta(card)
        card.next_week = _build_next_week(card)
        # Replace generic Linear risk strings with specific evidence-based explanations
        if card.status in ("at_risk", "off_track"):
            specific = _build_status_explanation(card)
            if specific:
                card.blockers = specific + [
                    b for b in card.blockers
                    if not any(generic in b for generic in [
                        "High staleness", "Low completion", "Low velocity", "Too much WIP"
                    ])
                ]

    # Sort: off_track first, then at_risk, then on_track; within group by health asc
    _order = {"off_track": 0, "at_risk": 1, "on_track": 2}
    project_cards.sort(key=lambda c: (_order[c.status], c.health_score))

    # ── 9. Capacity ─────────────────────────────────────────────────────────
    print("  🏖  Checking capacity...", file=sys.stderr)
    capacity = _collect_capacity()

    # ── 10. Decisions ────────────────────────────────────────────────────────
    decisions: list[dict] = []
    for card in project_cards:
        card.decision_needed = _detect_decision(card)
        if card.decision_needed:
            decisions.append({
                "project": card.name,
                "owner": card.owner,
                "text": card.decision_needed,
                "status": card.status,
                "eta_risk": card.eta_risk,
            })

    # ── 11. Cross-project risks ──────────────────────────────────────────────
    cross_project_risks: list[str] = []
    for sig in cross_project_signals:
        for blocker in sig.get("blockers", []):
            cross_project_risks.append(f"[{sig['title']}] {blocker}")
        for risk in sig.get("risks", []):
            cross_project_risks.append(f"[{sig['title']}] {risk}")

    # ── 12. Portfolio summary ────────────────────────────────────────────────
    summary = PortfolioSummary(
        total_projects=len(project_cards),
        on_track=sum(1 for c in project_cards if c.status == "on_track"),
        at_risk=sum(1 for c in project_cards if c.status == "at_risk"),
        off_track=sum(1 for c in project_cards if c.status == "off_track"),
        decisions_needed=len(decisions),
        top_risk=_build_bottom_line(project_cards, decisions),
    )

    report = SteeringReport(
        report_id=report_id,
        generated_at=datetime.now().isoformat(),
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        portfolio_summary=summary,
        projects=project_cards,
        decisions_needed=decisions,
        cross_project_risks=cross_project_risks,
        capacity_signals=capacity,
        sprint_signals=sprint_signals,
        sources=sources,
        errors=errors,
    )

    # ── 13. Render ──────────────────────────────────────────────────────────
    print("  🖨  Rendering report...", file=sys.stderr)
    try:
        report.rendered_markdown = render_markdown(report)
    except Exception as e:
        errors.append(f"markdown_render: {e}")

    try:
        report.rendered_html = render_html(report)
    except Exception as e:
        errors.append(f"html_render: {e}")

    print(f"✅ Steering report ready: {len(project_cards)} projects, "
          f"{len(decisions)} decisions needed", file=sys.stderr)
    return report


# ── Persistence ──────────────────────────────────────────────────────────────

def save_report(report: SteeringReport) -> dict[str, Path]:
    """
    Save the report to ~/.axeng/reports/steering/ (or configured output_dir).
    Returns {json: path, md: path, html: path}.
    """
    output_dir = Path(
        cfg_get("steering.output_dir", "~/.axeng/reports/steering")
    ).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = report.report_id   # "steering-2026-05-30"
    paths: dict[str, Path] = {}

    # JSON — structured data, loadable by API
    json_path = output_dir / f"{stem}.json"
    json_path.write_text(
        json.dumps(report_to_dict(report), indent=2, default=str),
        encoding="utf-8",
    )
    paths["json"] = json_path

    # Markdown — CLI output and Telegram
    if report.rendered_markdown:
        md_path = output_dir / f"{stem}.md"
        md_path.write_text(report.rendered_markdown, encoding="utf-8")
        paths["md"] = md_path

    # HTML — email body and browser view
    if report.rendered_html:
        html_path = output_dir / f"{stem}.html"
        html_path.write_text(report.rendered_html, encoding="utf-8")
        paths["html"] = html_path

    # Update rolling index file for API listing
    _update_index(output_dir, report)

    print(f"📁 Saved to {output_dir}", file=sys.stderr)
    return paths


def _update_index(output_dir: Path, report: SteeringReport) -> None:
    """Keep reports/steering/index.json up-to-date for API listing."""
    index_path = output_dir / "index.json"
    try:
        index: list[dict] = json.loads(index_path.read_text()) if index_path.exists() else []
    except Exception:
        index = []

    entry = {
        "id": report.report_id,
        "week_end": report.week_end,
        "week_start": report.week_start,
        "generated_at": report.generated_at,
        "title": f"Steering — {report.week_end}",
        "type": "steering",
        "summary": report.portfolio_summary.top_risk or "",
        "projects": report.portfolio_summary.total_projects,
        "decisions": report.portfolio_summary.decisions_needed,
        "sources": report.sources,
    }

    # Replace existing entry for same week, or prepend
    index = [e for e in index if e.get("id") != report.report_id]
    index.insert(0, entry)
    # Keep last 52 weeks
    index = index[:52]

    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def send_report(report: SteeringReport, paths: dict[str, Path]) -> bool:
    """
    Send the report via configured channel.
    Tries Gmail (HTML email) first, then Telegram.
    Returns True only if at least one delivery actually succeeded.
    Never raises — failures are printed to stderr.
    """
    import os, subprocess

    recipients: list = cfg_get("steering.recipients", [])
    any_sent = False

    # ── Gmail HTML email ────────────────────────────────────────────────────
    html_path = paths.get("html")
    if html_path and recipients:
        gmail_script = cfg_get(
            "email.gmail_script",
            "~/.axeng/skills/productivity/google-workspace/scripts/google_api.py"
        )
        gmail_path = Path(gmail_script).expanduser()
        if not gmail_path.exists():
            print(f"⚠️  Gmail script not found at {gmail_path} — skipping email", file=sys.stderr)
        else:
            subject = f"Engineering Update — {report.week_end}"
            for recipient in recipients:
                try:
                    result = subprocess.run(
                        [
                            sys.executable, str(gmail_path),
                            "gmail", "send",
                            "--to", recipient,
                            "--subject", subject,
                            "--html", str(html_path),
                        ],
                        capture_output=True, text=True, timeout=30,
                    )
                    if result.returncode == 0:
                        print(f"✉️  Sent to {recipient}", file=sys.stderr)
                        any_sent = True
                    else:
                        print(f"⚠️  Gmail send failed for {recipient}: {result.stderr[:200]}", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️  Gmail error for {recipient}: {e}", file=sys.stderr)

    # ── Telegram Markdown fallback ──────────────────────────────────────────
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id and report.rendered_markdown:
        excerpt = report.rendered_markdown[:4000]
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    "-d", f"chat_id={chat_id}",
                    "-d", f"text={excerpt}",
                    "-d", "parse_mode=Markdown",
                ],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                print("📨 Sent via Telegram", file=sys.stderr)
                any_sent = True
            else:
                print(f"⚠️  Telegram send failed: {result.stderr[:200]}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Telegram error: {e}", file=sys.stderr)

    if not any_sent:
        if not recipients and not (os.getenv("TELEGRAM_BOT_TOKEN")):
            print("⚠️  No delivery channels configured — set steering.recipients or TELEGRAM_BOT_TOKEN",
                  file=sys.stderr)
        else:
            print("⚠️  All delivery attempts failed — report saved locally only", file=sys.stderr)

    return any_sent


# ── CLI entry ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate steering report")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")
    parser.add_argument("--send", action="store_true", help="Send via email/Telegram after saving")
    parser.add_argument("--week-ending", help="ISO date e.g. 2026-05-30")
    args = parser.parse_args()

    week_end_date = date.fromisoformat(args.week_ending) if args.week_ending else None
    report = generate_steering_report(week_end_date)
    paths = save_report(report)

    if args.send:
        delivered = send_report(report, paths)
        if not delivered:
            sys.exit(1)   # non-zero so CLI caller can detect failure

    if args.json:
        print(json.dumps(report_to_dict(report), indent=2, default=str))
    else:
        print(report.rendered_markdown or "")
