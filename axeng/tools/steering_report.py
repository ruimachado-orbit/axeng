#!/usr/bin/env python3
"""
Steering Report — Portfolio Aggregator
Assembles per-project data from Linear, GitHub Issues, Granola, and risk signals,
scores each project, and renders the weekly executive document.

Architecture
────────────
The steering report is a 16-phase pipeline that builds a from-scratch snapshot each
week — no incremental state, no database dependency. Every phase can fail independently
and record a non-fatal error without aborting the generation.

Data flow (sequential — each phase enriches data for the next)::

  1. build_maps()              → project map (name ⇄ Linear ID ⇄ GitHub repos)
  2. linear_project_health()   → per-project metrics (completion, staleness, velocity)
  3. sprint signals            → team-wide sprint pulse (2-week cadence, not weekly)
  4. build project cards       → assemble initial cards with Linear data only
  5. github_commits_summary()  → attach commit counts to project repos
  6. enrich_with_issue_signals() → GitHub Issues risk signals attached to cards
  7. enrich_with_granola()     → meeting transcript intelligence (decisions/blockers/risks)
  8. re-score                  → run scoring model now that all signals are populated
  9. synthesize week deltas     → rule-based week_delta + next_week + status explanation
 10. detect decisions           → threshold-based decision prompts per project
 11. cross-project risks        → aggregate risks from Granola meeting context
 12. LLM narrative synthesis    → natural-language top_risk, client_summary, per-project prose
                                  (graceful fallback to rule-based if LLM unavailable)
 13. portfolio summary          → count on_track / at_risk / off_track
 14. render HTML + Markdown     → produce email-safe HTML and CLI Markdown
 15. persist to disk            → save JSON, MD, HTML to ~/.axeng/reports/steering/
 16. optional send              → Gmail HTML email, Telegram Markdown fallback

Scoring model (weights)
───────────────────────
    Linear delivery completion + velocity  … 35%
    Timeline alignment (work vs time)       … 25%
    Issue risk (inverted GitHub risk score)  … 20%
    Transcript signals (meeting tone caps)   … 15%
    Staleness penalty                       …  5%

    Team velocity trend is applied as a modifier after weighting:
      declining → −8pts, improving → +5pts
    Urgent transcript tone → caps score at ≤59 and status at at_risk

Signal sources
──────────────
    linear          — Linear GraphQL API (project metrics, sprints, milestones)
    github_issues   — GitHub GraphQL API (stale, unowned, overdue issues)
    github_commits  — GitHub REST API (commit activity per repo)
    granola         — Granola meeting notes (transcript attribution + LLM extraction)
    sprint          — sprint health predictions from Linear cycle data

Compatibility note
──────────────────
This module shares the project map (build_maps) and Linear data with the existing
engineering-manager weekly report (tools/weekly_report.py). The weekly report is
untouched and remains the primary team-facing summary. The steering report is a
separate CEO/executive-focused document with its own scoring, rendering, and delivery.

Entry point:  generate_steering_report(week_ending: date | None) -> SteeringReport
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get as cfg_get, llm_provider_order
from llm_gateway import call_with_fallback
from project_map import build_maps, all_repos, owner_of_project, repos_for_project, linear_project_ids
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
    InactiveGroup,
    IssueSignals,
    LinearSignals,
    PortfolioSummary,
    ProjectCard,
    ScoreTrend,
    Status,
    SteeringReport,
    TimelinePosition,
    TranscriptSignal,
    report_to_dict,
)

STEERING_RULES_PATH = Path(__file__).resolve().parents[2] / "prompts" / "steering-report-generation-rules.md"


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
        total_issues=metrics.get("total_issues", 0),
        completion_rate=metrics.get("completion_rate", 0.0),
        staleness_rate=metrics.get("staleness_rate", 0.0),
        stale_count=metrics.get("stale_count", 0),
        velocity=metrics.get("velocity", 0.0),
        in_progress=metrics.get("in_progress", 0),
        todo=metrics.get("todo", 0),
        completed=metrics.get("completed", 0),
        top_stale_issues=project_data.get("top_stale_issues", []),
        focus_issues=project_data.get("focus_issues", []),
        risks=project_data.get("risks", []),
        recently_completed_titles=project_data.get("recently_completed_titles", []),
    )


# ── Scoring (Phase 4 extends this) ──────────────────────────────────────────

def _score_project(
    linear: LinearSignals,
    issues: IssueSignals,
    time_pct: float,
    work_pct: float,
    transcript_signals: list[TranscriptSignal],
    commit_signals: CommitSignals | None = None,
    days_left: int | None = None,
    start_date: str | None = None,
    velocity_trend: str = "stable",
) -> tuple[float, Confidence, Status, Forecast]:
    """
    Score a project from delivery signals, not hygiene:
    shipped activity, completed scope, milestone achievability, and true blockers.
    Unassigned/stale issues do not directly affect status.
    Returns (health_score, confidence, status, forecast).
    """
    remaining_issues = max(0, linear.todo + linear.in_progress)
    transcript_blockers = [b for ts in transcript_signals for b in ts.blockers]
    blocked_count = len(transcript_blockers)
    timeline_gap = work_pct - time_pct
    commit_count = commit_signals.commits_this_week if commit_signals else 0
    recent_start = False
    if start_date:
        try:
            recent_start = (date.today() - date.fromisoformat(start_date[:10])).days <= 45
        except Exception:
            recent_start = False

    shipped_signal = min(100.0, linear.completion_rate + min(commit_count * 0.8, 25) + min(linear.completed * 4, 20))

    if work_pct >= 85:
        schedule_score = 92.0 if timeline_gap >= -15 else 80.0
    elif recent_start and (days_left or 0) > 120:
        schedule_score = 78.0
    elif timeline_gap >= 10:
        schedule_score = 100.0
    elif timeline_gap >= -5:
        schedule_score = 88.0
    elif timeline_gap >= -15:
        schedule_score = 72.0
    elif timeline_gap >= -25:
        schedule_score = 50.0
    else:
        schedule_score = 25.0

    velocity_score = 65.0
    if remaining_issues == 0:
        velocity_score = 100.0
    elif linear.velocity > 0:
        if linear.velocity >= remaining_issues:
            velocity_score = 100.0
        elif remaining_issues <= linear.velocity * 3:
            velocity_score = 88.0
        elif remaining_issues <= linear.velocity * 7:
            velocity_score = 72.0
        else:
            velocity_score = 48.0
    else:
        velocity_score = 55.0 if commit_count >= 10 else 25.0

    blockers_score = max(0.0, 100.0 - blocked_count * 24 - issues.overdue_count * 18)
    activity_score = 75.0
    if commit_count >= 20 or linear.completed >= 5:
        activity_score = 92.0
    elif commit_count >= 8 or linear.completed >= 2:
        activity_score = 80.0
    elif commit_count > 0 or linear.in_progress > 0:
        activity_score = 68.0
    elif recent_start and (days_left or 0) > 120:
        activity_score = 60.0
    else:
        activity_score = 35.0

    health_score = (
        shipped_signal * 0.30 +
        schedule_score * 0.25 +
        velocity_score * 0.20 +
        blockers_score * 0.15 +
        activity_score * 0.10
    )

    # Hard guards for clear delivery risk.
    if issues.overdue_count > 0 and work_pct < 95:
        health_score = min(health_score, 44)
    if blocked_count >= 2:
        health_score = min(health_score, 54)
    if work_pct >= 85 and remaining_issues <= 3 and issues.overdue_count == 0 and blocked_count == 0:
        health_score = max(health_score, 78)
    if recent_start and (days_left or 0) > 90 and commit_count >= 15 and linear.completed == 0 and issues.overdue_count == 0:
        health_score = max(health_score, 63)
    elif (days_left or 0) > 180 and commit_count >= 25 and linear.completed == 0 and issues.overdue_count == 0:
        health_score = max(health_score, 60)

    # Team velocity trend modifier.
    if velocity_trend == "declining":
        health_score = max(0, health_score - 5)
    elif velocity_trend == "improving":
        health_score = min(100, health_score + 3)

    health_score = round(min(max(health_score, 0), 100), 1)

    if issues.overdue_count > 0 and work_pct < 95:
        status = "off_track"
    elif blocked_count > 0:
        status = "at_risk"
    elif recent_start and (days_left or 0) > 90 and commit_count >= 15 and linear.completed == 0:
        status = "at_risk"
    elif health_score >= 70:
        status: Status = "on_track"
    elif health_score >= 45:
        status = "at_risk"
    else:
        status = "off_track"

    if health_score >= 75 and not transcript_blockers:
        confidence: Confidence = "high"
    elif health_score >= 45:
        confidence = "medium"
    else:
        confidence = "low"

    if status == "on_track":
        forecast: Forecast = "delivering_as_planned"
    elif transcript_blockers:
        forecast = "blocked_needs_escalation"
    elif issues.overdue_count > 0:
        forecast = "target_date_at_risk"
    else:
        forecast = "target_date_at_risk"

    return health_score, confidence, status, forecast


# ── Decision detection ───────────────────────────────────────────────────────

def _build_week_delta(card: ProjectCard) -> str | None:
    """
    Synthesise a clear one-sentence week summary that separates code activity
    (GitHub commits) from issue tracker activity (Linear/GitHub Issues).
    Uses '·' to join distinct signal groups.
    """
    bullets = _build_delivered_bullets(card)
    if bullets:
        return bullets[0]

    lin = card.linear_signals
    if lin.completed > 0:
        return f"Completed {lin.completed} issue{'s' if lin.completed != 1 else ''} this week."
    if lin.in_progress > 0:
        return f"Continued delivery on {lin.in_progress} in-progress issue{'s' if lin.in_progress != 1 else ''}."
    return None


def _build_next_week(card: ProjectCard) -> str | None:
    """
    Synthesise what's planned/committed for next week from:
    - Commitments extracted from Granola meeting notes
    - Linear in-progress + high-priority todo issues
    - Upcoming milestones
    """
    bullets = _build_planned_bullets(card)
    return bullets[0] if bullets else None


def _clean_work_label(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    text = text.split(" — ", 1)[-1]
    text = text.split(":", 1)[-1].strip() if text.split(":", 1)[0].lower().startswith(("feat", "fix", "chore", "docs", "refactor", "test", "build", "ci")) else text
    text = text.replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    if text:
        text = text[0].upper() + text[1:]
    return text.rstrip(".")


def _summarise_commit_messages(messages: list[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    skip_prefixes = ("Merge pull request", "Merge branch", "Merge remote", "chore: bump", "chore: update")
    for raw in messages:
        cleaned = _clean_work_label(raw)
        lowered = cleaned.lower()
        if not cleaned or lowered in seen:
            continue
        if any(cleaned.startswith(p) for p in skip_prefixes):
            continue
        seen.add(lowered)
        items.append(cleaned)
    return items[:15]


def _summarise_pr_titles(titles: list[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in titles:
        cleaned = _clean_work_label(raw)
        lowered = cleaned.lower()
        if not cleaned or lowered in seen:
            continue
        seen.add(lowered)
        items.append(cleaned)
    return items[:4]


def _raw_commit_descriptors(card: ProjectCard) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in (card.commit_signals.recent_pr_titles or []) + (card.commit_signals.recent_messages or []):
        text = " ".join(str(raw).split()).strip().rstrip(".")
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        items.append(text)
        if len(items) >= 3:
            break
    return items


def _summarise_issue_labels(labels: list[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in labels:
        cleaned = _clean_work_label(raw)
        lowered = cleaned.lower()
        if not cleaned or lowered in seen:
            continue
        seen.add(lowered)
        items.append(cleaned)
    return items[:5]


def _summarise_linear_completed(titles: list[str]) -> list[str]:
    """Clean Linear 'ID — title' strings into business-readable delivery items."""
    items: list[str] = []
    seen: set[str] = set()
    for raw in titles:
        # Strip the Linear identifier prefix (e.g. "ENG-123 — ")
        title = raw.split(" — ", 1)[-1].strip() if " — " in raw else raw.strip()
        cleaned = _clean_work_label(title)
        lowered = cleaned.lower()
        if not cleaned or lowered in seen:
            continue
        seen.add(lowered)
        items.append(cleaned)
    return items[:6]


def _summarise_transcript_delivery(card: ProjectCard) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    positive_verbs = (
        "shipped", "completed", "finished", "launched", "delivered",
        "implemented", "released", "added", "migrated", "fixed",
    )
    for ts in card.transcript_signals:
        candidates = ts.decisions + ts.commitments
        for raw in candidates:
            cleaned = _clean_work_label(raw)
            lowered = cleaned.lower()
            if not cleaned or lowered in seen:
                continue
            if any(v in lowered for v in positive_verbs) or ts.confidence_tone == "positive":
                seen.add(lowered)
                items.append(cleaned)
        if len(items) >= 3:
            break
    return items[:3]


def _summarise_transcript_risks(card: ProjectCard) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for ts in card.transcript_signals:
        for raw in ts.risks + ts.blockers:
            cleaned = _clean_work_label(raw)
            lowered = cleaned.lower()
            if not cleaned or lowered in seen:
                continue
            seen.add(lowered)
            items.append(cleaned)
        if len(items) >= 3:
            break
    return items[:3]


def _commit_activity_summary(card: ProjectCard) -> str | None:
    commit_items = _summarise_commit_messages(card.commit_signals.recent_messages)
    pr_items = _summarise_pr_titles(card.commit_signals.recent_pr_titles)
    if commit_items:
        lead = "; ".join(item.rstrip(".") for item in commit_items[:2])
        if card.commit_signals.commits_this_week > len(commit_items):
            lead += f"; {card.commit_signals.commits_this_week} commits merged"
        return lead

    if pr_items:
        lead = "; ".join(item.rstrip(".") for item in pr_items[:2])
        if card.commit_signals.commits_this_week > 0:
            lead += f"; {card.commit_signals.commits_this_week} commits merged"
        return lead

    if card.commit_signals.commits_this_week > 0:
        # Try cleaned commit messages one more time before giving up
        cleaned = _summarise_commit_messages(card.commit_signals.recent_messages)
        if cleaned:
            lead = "; ".join(item.rstrip(".") for item in cleaned[:3])
            if card.commit_signals.commits_this_week > len(cleaned):
                lead += f" ({card.commit_signals.commits_this_week} commits total)"
            return lead
        raw_items = _raw_commit_descriptors(card)
        if raw_items:
            return "; ".join(raw_items[:2]) + f" ({card.commit_signals.commits_this_week} commits)"
        repos = ", ".join(card.commit_signals.active_repos[:3]) or "active repositories"
        return f"{card.commit_signals.commits_this_week} commits in {repos} — message metadata unavailable"

    return None


def _build_delivered_bullets(card: ProjectCard) -> list[str]:
    """
    Build 3–6 bullets of what was delivered this week.
    Source priority:
      1. Linear issues completed this week (business-language titles)
      2. GitHub issues closed this week (feature/fix names)
      3. Merged PRs (PR titles)
      4. Commit messages (lower signal — last resort)
      5. Granola transcript delivery items
    Evidence summary appended last so counts never replace outcomes.
    """
    bullets: list[str] = []
    seen_lower: set[str] = set()
    lin = card.linear_signals
    gh = card.issue_signals
    cs = card.commit_signals

    def _add(text: str) -> bool:
        t = text.rstrip(".")
        low = t.lower()
        if not t or low in seen_lower:
            return False
        seen_lower.add(low)
        bullets.append(t + ".")
        return True

    # 1. Linear completed this week — highest signal, business language
    for item in _summarise_linear_completed(lin.recently_completed_titles):
        if len(bullets) >= 5:
            break
        _add(item)

    # 2. GitHub issues closed this week
    for item in _summarise_issue_labels(gh.recently_closed):
        if len(bullets) >= 5:
            break
        _add(item)

    # 3. Merged PRs (often the clearest signal for what shipped)
    for item in _summarise_pr_titles(cs.recent_pr_titles):
        if len(bullets) >= 5:
            break
        _add(item)

    # 4. Commit messages — lower signal, only if we still have room
    if len(bullets) < 3:
        for item in _summarise_commit_messages(cs.recent_messages):
            if len(bullets) >= 4:
                break
            _add(item)

    # 5. Granola transcript delivery mentions
    for item in _summarise_transcript_delivery(card):
        if len(bullets) >= 5:
            break
        _add(item)

    # Fallback: activity summary if nothing concrete was found
    if not bullets:
        commit_summary = _commit_activity_summary(card)
        if commit_summary:
            _add(commit_summary)

    # Evidence footer — counts only, appended after real outcomes
    evidence_parts: list[str] = []
    if lin.completed > 0 and not lin.recently_completed_titles:
        evidence_parts.append(f"{lin.completed} Linear issue{'s' if lin.completed != 1 else ''} marked done")
    if gh.closed_this_week > 0 and not gh.recently_closed:
        evidence_parts.append(f"{gh.closed_this_week} GitHub issue{'s' if gh.closed_this_week != 1 else ''} closed")
    if cs.commits_this_week > 0 and not cs.recent_pr_titles and not cs.recent_messages:
        repo_count = len(cs.active_repos)
        evidence_parts.append(
            f"{cs.commits_this_week} commit{'s' if cs.commits_this_week != 1 else ''} merged"
            + (f" across {repo_count} repo{'s' if repo_count != 1 else ''}" if repo_count else "")
        )
    if evidence_parts and len(bullets) < 6:
        bullets.append("Evidence: " + "; ".join(evidence_parts) + ".")

    if not bullets and lin.in_progress > 0:
        bullets.append(f"Continued active work on {lin.in_progress} in-progress issue{'s' if lin.in_progress != 1 else ''}.")
    return bullets[:6]


def _build_planned_bullets(card: ProjectCard) -> list[str]:
    """
    Build 2–4 bullets of what's planned for next week.
    Source priority:
      1. Granola meeting commitments (explicit team promises)
      2. Linear in-progress issues (already started, highest likelihood to ship)
      3. Linear focus issues (high-priority todo)
      4. Upcoming milestone (as deadline anchor)
    Commits are NOT a source here — next-week plan is intent, not past activity.
    """
    bullets: list[str] = []
    seen_lower: set[str] = set()

    def _add(text: str) -> bool:
        t = text.rstrip(".")
        low = t.lower()
        if not t or low in seen_lower:
            return False
        seen_lower.add(low)
        bullets.append(t + ".")
        return True

    # 1. Explicit commitments from Granola meeting notes
    for ts in card.transcript_signals:
        for commitment in ts.commitments[:3]:
            if commitment and len(bullets) < 3:
                _add(commitment)
        if len(bullets) >= 2:
            break

    # 2. Linear in-progress issues — most likely to deliver next week
    lin = card.linear_signals
    in_progress_issues = [i for i in (lin.focus_issues or []) if "(P" in i]
    if not in_progress_issues and lin.in_progress > 0:
        # No titled in-progress, use count
        _add(f"Complete {lin.in_progress} issue{'s' if lin.in_progress != 1 else ''} currently in progress")

    # 3. High-priority focus issues by name
    for issue in lin.focus_issues[:4]:
        if len(bullets) >= 4:
            break
        # Strip "(Pn)" priority suffix for clean display
        title = issue.split(" (P")[0].strip()
        cleaned = _clean_work_label(title.split(" — ", 1)[-1] if " — " in title else title)
        if cleaned:
            _add(f"Deliver {cleaned}")

    # 4. Next upcoming milestone as deadline anchor
    ms = _current_milestone(card)
    if ms and ms.get("target_date") and len(bullets) < 4:
        _add(f"Target milestone '{ms['name']}' by {ms['target_date']}")

    return bullets[:4]


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


def _dedupe_blockers(blockers: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    has_stale = False
    has_no_velocity = False
    for raw in blockers:
        text = " ".join(str(raw).split()).strip()
        if not text:
            continue
        lower = text.lower()
        if "stale" in lower:
            if has_stale:
                continue
            has_stale = True
        if "no velocity" in lower or "no issue transitions" in lower:
            if has_no_velocity:
                continue
            has_no_velocity = True
        if lower in seen:
            continue
        seen.add(lower)
        deduped.append(text)
    return deduped[:4]


def _detect_decision(card: ProjectCard) -> str | None:
    """Return a one-line decision prompt if the project needs one, else None."""
    if card.forecast == "blocked_needs_escalation":
        blocker = card.blockers[0] if card.blockers else "blocker"
        return f"Unblock {card.name}: {blocker}"
    # Only fire unowned_assign_now if there are actually unowned issues
    if card.forecast == "unowned_assign_now" and card.issue_signals.unowned_count > 0 and card.linear_signals.completion_rate < 80:
        return f"Assign owner for {card.name} — {card.issue_signals.unowned_count} unowned issues"
    if card.forecast == "target_date_at_risk" and (card.days_left or 99) < 21:
        return f"Decide: rescope {card.name} or accept date slip ({card.days_left}d left)"
    if card.eta_risk in ("high", "critical") and card.status != "on_track":
        return f"Review {card.name} timeline — {card.eta_risk} ETA risk"
    return None


# ── Bottom line synthesis ────────────────────────────────────────────────────

def _build_bottom_line(projects: list[ProjectCard], decisions: list[dict]) -> str:
    ranked = sorted(
        projects,
        key=lambda p: (
            0 if p.status == "off_track" else 1 if p.status == "at_risk" else 2,
            p.days_left if p.days_left is not None else 9999,
            p.health_score,
        ),
    )
    risk_lines: list[str] = []
    for p in ranked:
        if p.status == "on_track" and len(risk_lines) >= 1:
            continue
        if p.days_left is not None and p.days_left < 0:
            risk_lines.append(f"{p.name} missed target date by {abs(p.days_left)}d.")
        elif p.issue_signals.unowned_count > 0 and p.linear_signals.completion_rate < 80:
            risk_lines.append(f"{p.name} has {p.issue_signals.unowned_count} unowned issues.")
        elif p.blockers:
            risk_lines.append(f"{p.name} is blocked: {p.blockers[0]}.")
        elif p.status != "on_track":
            risk_lines.append(f"{p.name} is {p.status.replace('_', ' ')} with {int(p.work_progress_pct)}% complete.")
        if len(risk_lines) >= 3:
            break

    if not risk_lines:
        return f"Portfolio steady: {sum(1 for p in projects if p.status == 'on_track')} projects on track, no immediate escalation required."

    return " Top risks: " + " ".join(f"{i + 1}. {line}" for i, line in enumerate(risk_lines))


# ── Portfolio-level weekly summaries ────────────────────────────────────────

def _build_this_week_summary(cards: list[ProjectCard]) -> list[str]:
    """
    3-5 portfolio-level bullet points covering code activity, issue tracker
    activity, milestone progress, and risk signals. Each bullet is scoped to
    a single signal source so they never double-count.
    """
    bullets: list[str] = []

    success_projects = [c for c in cards if c.status == "on_track" and c.delivered_bullets]
    if success_projects:
        for c in success_projects[:3]:
            bullets.append(f"{c.name}: {c.delivered_bullets[0].rstrip('.')}.")

    active_dev = [
        c for c in cards
        if c.commit_signals.commits_this_week > 0 and not c.delivered_bullets
    ]
    for c in active_dev[:2]:
        commit_summary = _commit_activity_summary(c)
        if commit_summary:
            bullets.append(f"{c.name}: {commit_summary.rstrip('.')}.")

    from datetime import date as _d, timedelta
    week_ago = (_d.today() - timedelta(days=7)).isoformat()
    today = _d.today().isoformat()
    ms_passed = []
    for c in cards:
        for m in c.milestones:
            if week_ago <= m.get("target_date", "") <= today:
                ms_passed.append(f"{c.name}: {m['name']}")
    if ms_passed:
        bullets.append(f"Milestones reached: {', '.join(ms_passed[:3])}")

    return bullets[:5]


def _build_client_summary(cards: list[ProjectCard], inactive_group: InactiveGroup | None) -> str:
    """
    Build a structured weekly summary as newline-separated labeled sections.
    Format understood by both the HTML renderer and Markdown renderer:
      §Delivered
      ProjectName: bullet
      ProjectName: bullet
      §Committed Next
      ...
      §Risks
      ...
      §Inactive
      ...
    """
    sections: list[str] = []

    # ── Delivered ──────────────────────────────────────────────
    delivered_lines: list[str] = []
    for c in cards:
        bullets = c.delivered_bullets
        if not bullets:
            continue
        # Up to 5 bullets per project, each on its own line
        for b in bullets[:5]:
            delivered_lines.append(f"{c.name}: {b.rstrip('.')}")
    if delivered_lines:
        sections.append("§Delivered\n" + "\n".join(delivered_lines))

    # ── Committed Next ─────────────────────────────────────────
    committed_lines: list[str] = []
    for c in cards:
        for ts in c.transcript_signals:
            for item in ts.commitments[:2]:
                if item:
                    committed_lines.append(f"{c.name}: {item.rstrip('.')}")
            if committed_lines:
                break
        if len(committed_lines) >= 4:
            break
    if not committed_lines:
        for c in cards:
            if c.planned_bullets:
                committed_lines.append(f"{c.name}: {c.planned_bullets[0].rstrip('.')}")
            if len(committed_lines) >= 4:
                break
    if committed_lines:
        sections.append("§Committed Next\n" + "\n".join(committed_lines[:4]))

    # ── Risks ─────────────────────────────────────────────────
    risk_lines: list[str] = []
    for c in cards:
        if c.days_left is not None and c.days_left < 0:
            risk_lines.append(f"{c.name} missed its target date by {abs(c.days_left)}d")
        elif c.status == "at_risk" and c.blockers:
            risk_lines.append(f"{c.name}: {c.blockers[0].rstrip('.')}")
        elif c.status == "at_risk":
            transcript_risks = _summarise_transcript_risks(c)
            if transcript_risks:
                risk_lines.append(f"{c.name}: {transcript_risks[0].rstrip('.')}")
    if risk_lines:
        sections.append("§Risks\n" + "\n".join(risk_lines[:3]))

    # ── Inactive ──────────────────────────────────────────────
    if inactive_group and inactive_group.count > 0:
        names = ", ".join(inactive_group.projects[:4])
        sections.append(f"§Inactive\n{inactive_group.count} project{'s' if inactive_group.count != 1 else ''} with no measurable progress: {names}")

    return "\n\n".join(sections)


def _build_next_week_summary(cards: list[ProjectCard]) -> list[str]:
    """
    3-5 bullet points of what's planned / committed for next week.
    Aggregates: meeting commitments, upcoming milestones, in-progress work.
    """
    bullets: list[str] = []
    from datetime import date as _d, timedelta
    today = _d.today().isoformat()
    next_2w = (_d.today() + timedelta(days=14)).isoformat()

    planned = []
    for c in cards:
        for item in _build_planned_bullets(c)[:1]:
            planned.append(f"{c.name}: {item.rstrip('.')}")
    if planned:
        bullets.append("Planned next: " + "; ".join(planned[:3]) + ".")

    # Milestones due in next 2 weeks
    upcoming_ms = []
    for c in cards:
        for m in sorted(c.milestones, key=lambda m: m.get("target_date", "")):
            if today <= m.get("target_date", "") <= next_2w:
                upcoming_ms.append(f"{c.name}: {m['name']} ({m['target_date']})")
                break
    if upcoming_ms:
        bullets.append(f"Milestones due next 2 weeks: {', '.join(upcoming_ms[:4])}")

    blocked = [c for c in cards if c.decision_needed]
    if blocked:
        bullets.append(f"Blocked on decision: {', '.join(c.name for c in blocked[:3])}")

    return bullets[:5]


# ── LLM narrative synthesis ──────────────────────────────────────────────────

def _load_steering_system_prompt() -> str:
    base = (
        "You are an Engineering Manager chief-of-staff writing a concise executive steering document. "
        "Be direct, evidence-driven, and decision-focused. No filler. No emojis. No markdown headers. "
        "All prose should be one or two tight sentences per field — suitable for a busy CEO skimming on mobile."
    )
    try:
        rules = STEERING_RULES_PATH.read_text(encoding="utf-8").strip()
        if rules:
            return base + "\n\n" + rules
    except Exception:
        pass
    return base


_STEERING_SYSTEM = _load_steering_system_prompt()

def _llm_synthesize_narrative(
    project_cards: list[ProjectCard],
    decisions: list[dict],
    week_end: str,
) -> dict | None:
    """
    Call the LLM to synthesize:
      - top_risk: one-sentence portfolio bottom line
      - this_week_summary: list[str] bullets
      - next_week_summary: list[str] bullets
      - per_project: dict[name -> {week_delta, next_week, delivered_bullets, planned_bullets, blockers}]

    Returns None if LLM is unavailable (callers fall back to rule-based).
    """
    # Build a compact JSON snapshot of the portfolio for the prompt
    snapshot = []
    for c in project_cards:
        snapshot.append({
            "name": c.name,
            "owner": c.owner,
            "status": c.status,
            "health_score": round(c.health_score),
            "days_left": c.days_left,
            "work_pct": round(c.work_progress_pct),
            "time_pct": round(c.time_progress_pct),
            "eta_risk": c.eta_risk,
            # Delivery evidence — pre-cleaned and ranked by signal quality
            "linear_completed_this_week": c.linear_signals.recently_completed_titles[:6],
            "github_issues_closed_this_week": c.issue_signals.recently_closed[:5],
            "merged_prs": c.commit_signals.recent_pr_titles[:5],
            "commits_this_week": c.commit_signals.commits_this_week,
            # Pre-cleaned commit summaries (conventional-commit prefix stripped, deduped)
            # Group these by theme — do NOT list one bullet per commit
            "commit_summaries": _summarise_commit_messages(c.commit_signals.recent_messages)[:15],
            # Rule-based delivery bullets already derived — improve/rewrite these, don't ignore
            "rule_based_delivered_bullets": c.delivered_bullets[:6],
            # Work in flight — basis for next-week plan
            "issues_in_progress": c.linear_signals.in_progress,
            "issues_todo": c.linear_signals.todo,
            "focus_issues": c.linear_signals.focus_issues[:4],
            # Counts for context
            "issues_completed_total": c.linear_signals.completed,
            "velocity": round(c.linear_signals.velocity, 2),
            "staleness_rate": round(c.linear_signals.staleness_rate),
            "unowned_issues": c.issue_signals.unowned_count,
            "blocked_threads": c.issue_signals.blocked_threads,
            "backlog_growth": c.issue_signals.backlog_growth,
            "github_issues_opened": c.issue_signals.opened_this_week,
            "blockers": c.blockers[:3],
            "meeting_signals": [
                {
                    "title": ts.title,
                    "date": ts.note_date,
                    "decisions": ts.decisions[:3],
                    "risks": ts.risks[:3],
                    "commitments": ts.commitments[:3],
                }
                for ts in c.transcript_signals[:3]
            ],
            "milestones": [
                {"name": m["name"], "target_date": m.get("target_date")}
                for m in c.milestones[:4]
            ],
            "decision_needed": c.decision_needed,
        })

    decisions_text = json.dumps(decisions, ensure_ascii=False)
    snapshot_text = json.dumps(snapshot, ensure_ascii=False, indent=2)

    prompt = f"""\
Week ending: {week_end}
Portfolio decisions needed: {len(decisions)}

Project data:
{snapshot_text}

Decisions flagged:
{decisions_text}

Respond with a JSON object with exactly these keys:

{{
  "top_risk": "<one sentence: portfolio bottom line for the CEO — what matters most this week>",
  "client_summary": "§Delivered\n<ProjectName>: <bullet>\n<ProjectName>: <bullet>\n\n§Committed Next\n<ProjectName>: <commitment>\n\n§Risks\n<ProjectName>: <risk>\n\n§Inactive\n<count> projects with no activity: <names>",
  "this_week_summary": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
  "next_week_summary": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
  "per_project": {{
    "<project name>": {{
      "week_delta": "<one sentence: what happened this week — commits, issues closed, backlog movement>",
      "delivered_bullets": ["<2-5 bullets: what was actually delivered or concretely advanced this week>"],
      "next_week": "<one sentence: what's committed or planned for next week>",
      "planned_bullets": ["<1-4 bullets: what is planned next week>"],
      "blockers": ["<specific blocker 1>", "<specific blocker 2>"]
    }}
  }}
}}

Rules:
- top_risk must name the single most urgent issue or decision. If all green, say so.
- client_summary: structured plain-English summary using §Section headers. Sections: §Delivered (one line per project, up to 5 bullets each, format "ProjectName: what was done"), §Committed Next (explicit promises from meetings or planned_bullets, one line per project), §Risks (at-risk/blocked projects, one line each), §Inactive (projects with no activity, optional). Omit a section entirely if it has no content. No jargon, no internal IDs. Each project gets its own line — never join multiple projects into one sentence.
- this_week_summary: 3-5 bullets, portfolio-level, specific numbers where available.
- next_week_summary: 3-5 bullets, what the team is committed to delivering.
- per_project week_delta: one tight sentence summarising the week — what shipped, what moved, what didn't.
- per_project delivered_bullets: 2-5 bullets summarising what was delivered this week as FEATURES and BUG FIXES.
  Each bullet = one shipped capability or one fixed problem. NOT one commit per bullet.

  Step 1 — collect all evidence:
    • linear_completed_this_week: completed Linear issues (highest confidence)
    • github_issues_closed_this_week: closed GitHub issues
    • merged_prs: merged pull requests
    • commit_summaries: pre-cleaned commit messages (use when the above are sparse)

  Step 2 — GROUP by theme. Multiple commits/issues that relate to the same feature or area belong in one bullet.
    Example grouping from commits:
      "Open RecordSessionPaymentDialog from calendar preview mark paid button"
      "Add verify, mark paid, revert payment actions to calendar preview popup"
      "Add status action buttons to calendar session preview popup"
    → One bullet: "Added payment action buttons (verify, mark paid, revert) to calendar session preview"

    Example grouping:
      "Fix move hasPrice declaration before first use to fix TDZ error"
      "Fix improve session booking validation and pdf export"
      "Fix keep qualified therapists selected in session form"
    → One bullet: "Fixed session booking validation, therapist selection, and PDF export issues"

    Example grouping:
      "Rework session booking flow with client_arrived/missed, invoice status tracking, and decoupled consultation mode"
      "Add client_arrived and client_missed session statuses"
    → One bullet: "Reworked session booking flow — added client arrived/missed statuses, invoice tracking, and decoupled consultation mode"

  Step 3 — write each bullet as: "[Verb] [what] — [brief business context if helpful]"
    Good verbs: Added, Shipped, Fixed, Improved, Completed, Reworked, Resolved, Launched
    Bad: "Development continued", "Work was done", "X commits merged"

  ONLY write "No delivery evidence available this week." if commit_summaries is empty AND commits_this_week == 0.
  If commit_summaries is non-empty, you MUST group and summarise them — do not skip or write a fallback message.
- per_project next_week: one sentence: what is the team committed to deliver next week.
- per_project planned_bullets: 2-4 concrete next-week bullets.
  Sources in order: (1) meeting_signals[].commitments — explicit promises made in meetings; (2) focus_issues — work in progress or high-priority todo; (3) upcoming milestone as deadline anchor.
  DO NOT use commit_summaries or merged_prs as a source for next-week — those are past activity.
  Each bullet: "Complete X", "Ship Y", "Resolve Z".
- per_project blockers: only include if genuinely blocked on an external dependency or decision; empty list if none.
- Use only information provided. Do not invent issue names, PR titles, or outcomes not present in the data.
"""

    try:
        result = call_with_fallback(
            prompt,
            providers=llm_provider_order(),
            system=_STEERING_SYSTEM,
            json_output=True,
            max_tokens=3500,
            temperature=0.3,
        )
        if not result.get("ok"):
            print(f"  ⚠  LLM unavailable for narrative: {result.get('error')} — using rule-based", file=sys.stderr)
            return None

        text = result["text"].strip()
        # Strip markdown code fences if the model wrapped the JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠  LLM narrative synthesis failed: {e} — using rule-based", file=sys.stderr)
        return None


def _apply_llm_narrative(
    project_cards: list[ProjectCard],
    llm: dict,
) -> None:
    """Overwrite rule-based fields on each card with LLM-synthesized prose."""
    per_project = llm.get("per_project", {})
    for card in project_cards:
        p = per_project.get(card.name)
        if not p:
            continue
        if p.get("week_delta"):
            card.week_delta = p["week_delta"]
        if p.get("delivered_bullets"):
            card.delivered_bullets = [str(item) for item in p["delivered_bullets"][:5] if str(item).strip()]
        if p.get("next_week"):
            card.next_week = p["next_week"]
        if p.get("planned_bullets"):
            card.planned_bullets = [str(item) for item in p["planned_bullets"][:4] if str(item).strip()]
        if p.get("blockers"):
            # Prepend LLM blockers but keep any existing evidence-based ones not already covered
            existing = {b.lower() for b in card.blockers}
            new_blockers = [b for b in p["blockers"] if b.lower() not in existing]
            card.blockers = new_blockers + card.blockers


# ── Trend detection ──────────────────────────────────────────────────────────

def _load_previous_scores(report_id: str) -> dict[str, float]:
    """Load health scores from the previous week's report JSON.
    Returns {project_name: health_score} or empty dict if unavailable."""
    try:
        output_dir = Path(
            cfg_get("steering.output_dir", "~/.axeng/reports/steering")
        ).expanduser()
        index_path = output_dir / "index.json"
        if not index_path.exists():
            return {}

        index = json.loads(index_path.read_text())
        # index is sorted newest-first; grab the entry before the current report_id
        prev = None
        for i, entry in enumerate(index):
            if entry.get("id") == report_id and i + 1 < len(index):
                prev = index[i + 1]
                break

        if not prev:
            return {}

        prev_path = output_dir / f"{prev['id']}.json"
        if not prev_path.exists():
            return {}

        prev_data = json.loads(prev_path.read_text())
        return {
            p.get("name", ""): p.get("health_score", 0)
            for p in prev_data.get("projects", [])
        }
    except Exception:
        return {}


def _compute_score_trends(
    project_cards: list[ProjectCard],
    report_id: str,
) -> None:
    """Attach ScoreTrend to each card by comparing with previous week's scores."""
    previous = _load_previous_scores(report_id)
    if not previous:
        return

    for card in project_cards:
        prev_score = previous.get(card.name)
        if prev_score is None:
            card.score_trend = ScoreTrend(
                score=card.health_score, movement="new", delta=0, display=""
            )
            continue

        delta = int(card.health_score - prev_score)
        if delta > 3:
            movement: Literal["up", "down", "flat", "new"] = "up"
            display = f"↑{delta}"
        elif delta < -3:
            movement = "down"
            display = f"↓{abs(delta)}"
        else:
            movement = "flat"
            display = "—"

        card.score_trend = ScoreTrend(
            previous_score=prev_score,
            previous_week_id=None,
            score=card.health_score,
            movement=movement,
            delta=delta,
            display=display,
        )


# ── Inactive projects ─────────────────────────────────────────────────────────

def _build_inactive_group(cards: list[ProjectCard]) -> InactiveGroup | None:
    """Group stalled/incubation projects into a single collapsed view."""
    inactive = [c for c in cards if c.is_inactive]
    if not inactive:
        return None

    count = len(inactive)
    names = [p.name for p in inactive]
    if count == 1:
        summary = f"{names[0]} — no commits or issue activity this week"
    elif count == 2:
        summary = f"{count} projects with no activity: {names[0]} and {names[1]}"
    elif count <= 4:
        summary = f"{count} projects stalled: {', '.join(names[:3])}"
    else:
        summary = f"{count} projects have no measurable progress this week"

    return InactiveGroup(projects=names, count=count, summary=summary)


# ── Portfolio risks ───────────────────────────────────────────────────────────

def _build_portfolio_risks(
    cards: list[ProjectCard],
    inactive_group: InactiveGroup | None,
) -> list[str]:
    """Synthesize milestone/delivery risks, not hygiene warnings."""
    risks: list[str] = []

    # Inactive project group
    if inactive_group and inactive_group.count >= 2:
        risks.append(inactive_group.summary)

    # Velocity collapse — projects where work% < time% significantly
    collapsing = [
        c for c in cards
        if c.time_progress_pct > 20 and c.work_progress_pct < c.time_progress_pct - 20
        and not c.is_inactive
    ]
    if collapsing:
        names = ", ".join(c.name for c in collapsing[:3])
        risks.append(f"Velocity deficit: {names} have work significantly behind elapsed time")

    # Downstream cascade — off_track projects with dependents or ETA critical
    critical_timeline = [
        c for c in cards
        if c.eta_risk == "critical" and c.status in ("at_risk", "off_track")
    ]
    if critical_timeline:
        names = ", ".join(c.name for c in critical_timeline[:3])
        risks.append(f"Timeline risk: {names} target date(s) have passed — downstream impact likely")

    return risks[:5]


# ── Leadership priorities ─────────────────────────────────────────────────────

def _build_leadership_priorities(
    cards: list[ProjectCard],
    decisions: list[dict],
) -> list[str]:
    """Rank the top 3 most important actions for leadership this week."""
    priorities: list[str] = []

    # Priority candidates from decisions + off_track + critical ETA
    candidates: list[tuple[int, str]] = []
    # Priority score: off_track=3, at_risk=2, decision=3, critical_eta=3, days_left negative=2
    for c in cards:
        pscore = 0
        if c.status == "off_track":
            pscore += 30
        elif c.status == "at_risk":
            pscore += 15
        if c.decision_needed:
            pscore += 25
        if c.eta_risk == "critical":
            pscore += 20
        elif c.eta_risk == "high":
            pscore += 10
        if c.days_left is not None and c.days_left < 0:
            pscore += 15
        elif c.days_left is not None and c.days_left < 7:
            pscore += 8

        if pscore <= 0:
            continue

        text = c.decision_needed or (
            f"Review {c.name} — "
            + (f"past deadline by {abs(c.days_left)}d" if c.days_left is not None and c.days_left < 0 else f"{c.status.replace('_', ' ')}")
        )
        candidates.append((pscore, text))

    # Sort by priority score descending, take top 3
    candidates.sort(key=lambda x: x[0], reverse=True)
    for i, (_, text) in enumerate(candidates[:3]):
        priorities.append(f"{i + 1}. {text}")

    return priorities[:3]


# ── Score methodology ─────────────────────────────────────────────────────────

_SCORE_METHODOLOGY = (
    "Scores prioritize delivery confidence: completed vs remaining scope, time to target, current velocity, "
    "and concrete blockers. Stale or unowned issues are light penalties, not dominant signals. "
    "≥70 = On Track, 45–69 = At Risk, <45 = Off Track."
)

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
        if health_result.get("mode") == "teams":
            errors.append("linear: no Linear projects returned for this token/workspace")
        if not linear_projects:
            errors.append("linear: project health returned 0 projects")
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

    # Build indexes for fast lookup. Prefer ID matching because names can drift.
    linear_by_name = {p["name"]: p for p in linear_projects}
    linear_by_id = {p["id"]: p for p in linear_projects if p.get("id")}
    configured_project_ids = linear_project_ids()

    # ── 4. Build project cards ──────────────────────────────────────────────
    print("  🃏 Building project cards...", file=sys.stderr)
    project_cards: list[ProjectCard] = []

    # Only include projects explicitly configured in project_ids.
    # This keeps the steering report focused — no noise from test projects,
    # onboarding, or internal tooling that isn't part of the portfolio.
    configured_projects = list(linear_github_map.keys())
    missing_project_ids = [name for name in configured_projects if not configured_project_ids.get(name)]
    if missing_project_ids:
        errors.append(
            "linear: missing configured project_ids for "
            + ", ".join(missing_project_ids[:6])
            + (f" (+{len(missing_project_ids) - 6} more)" if len(missing_project_ids) > 6 else "")
        )

    for proj_name in configured_projects:
        map_entry = linear_github_map.get(proj_name, {})
        configured_project_id = configured_project_ids.get(proj_name)
        lin_data = (
            linear_by_id.get(configured_project_id, {})
            if configured_project_id
            else linear_by_name.get(proj_name, {})
        )
        if not lin_data:
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
        blockers: list[str] = []
        health_signals: list[str] = list(linear_signals.risks)
        if linear_signals.top_stale_issues:
            health_signals.append(
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
            linear_state=lin_data.get("state"),
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
            health_signals=health_signals,
            evidence=evidence,
        )
        project_cards.append(card)

    # ── 5. Attach velocity context to project cards ─────────────────────────
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
        by_repo = commits_data.get("by_repo", {})
        for card in project_cards:
            if not card.repos:
                continue
            active = [r for r in card.repos if (by_repo.get(r, {}) or {}).get("count", 0) > 0]
            quiet = [r for r in card.repos if (by_repo.get(r, {}) or {}).get("count", 0) == 0]
            total = sum((by_repo.get(r, {}) or {}).get("count", 0) for r in card.repos)
            recent_messages: list[str] = []
            recent_pr_titles: list[str] = []
            for repo in card.repos:
                recent_messages.extend((by_repo.get(repo, {}) or {}).get("recent_messages", [])[:8])
                recent_pr_titles.extend((by_repo.get(repo, {}) or {}).get("recent_pr_titles", [])[:6])
            card.commit_signals = CommitSignals(
                commits_this_week=total,
                active_repos=active,
                quiet_repos=quiet,
                recent_messages=recent_messages[:16],
                recent_pr_titles=recent_pr_titles[:10],
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

    # ── 8. Granola transcript enrichment ────────────────────────────────────
    cross_project_signals: list[dict] = []
    try:
        project_cards, cross_project_signals = enrich_with_granola(
            project_cards, week_start.isoformat(), week_end.isoformat()
        )
        sources.append("granola")
    except Exception as e:
        errors.append(f"granola: {e}")

    # ── 9. Re-score with all signals now populated ───────────────────────────
    print("  🧮 Scoring projects...", file=sys.stderr)
    for card in project_cards:
        health_score, confidence, status, forecast = _score_project(
            card.linear_signals,
            card.issue_signals,
            card.time_progress_pct,
            card.work_progress_pct,
            card.transcript_signals,
            commit_signals=card.commit_signals,
            days_left=card.days_left,
            start_date=card.start_date,
            velocity_trend=sprint_signals.velocity_trend,
        )
        card.health_score = health_score
        card.confidence = confidence
        card.status = status
        card.forecast = forecast
        # Re-derive eta_risk now that issue signals are included
        card.eta_risk = _compute_eta_risk(card.days_left, card.timeline_position)
        # Set is_inactive flag (was a property, now a stored field for serialization)
        card.is_inactive = (
            card.linear_signals.velocity == 0
            and card.commit_signals.commits_this_week == 0
            and card.linear_signals.in_progress == 0
        )

    # Build synthesised week summary + next week forecast + status explanation
    for card in project_cards:
        card.week_delta = _build_week_delta(card)
        card.delivered_bullets = _build_delivered_bullets(card)
        card.next_week = _build_next_week(card)
        card.planned_bullets = _build_planned_bullets(card)
        # Replace generic Linear risk strings with specific evidence-based explanations
        if card.status in ("at_risk", "off_track"):
            specific = _build_status_explanation(card)
            if specific:
                card.health_signals = specific + card.health_signals
        if card.issue_signals.stale_count > 0:
            card.health_signals.append(
                f"{card.issue_signals.stale_count} key issues stale for more than 7 days."
            )
        if card.linear_signals.velocity == 0 and card.linear_signals.completed == 0:
            card.health_signals.append("No issue transitions recorded this week.")
        if card.issue_signals.unowned_count > 0:
            card.health_signals.append(
                f"{card.issue_signals.unowned_count} unassigned issue{'s' if card.issue_signals.unowned_count != 1 else ''} remain in backlog."
            )
        card.blockers = _dedupe_blockers(card.blockers)
        card.health_signals = _dedupe_blockers(card.health_signals)

    # Sort: off_track first, then at_risk, then on_track; within group by health asc
    _order = {"off_track": 0, "at_risk": 1, "on_track": 2}
    project_cards.sort(key=lambda c: (_order[c.status], c.health_score))

    # ── 10. Inactive group ────────────────────────────────────────────────────
    inactive_group = _build_inactive_group(project_cards)

    # ── 11. Week-over-week score trends ───────────────────────────────────────
    print("  📈 Computing score trends...", file=sys.stderr)
    _compute_score_trends(project_cards, report_id)

    # ── 12. Capacity ─────────────────────────────────────────────────────────
    print("  🏖  Checking capacity...", file=sys.stderr)
    capacity = _collect_capacity()

    # ── 13. Decisions ────────────────────────────────────────────────────────
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

    # ── 14. Cross-project risks ──────────────────────────────────────────────
    cross_project_risks: list[str] = []
    for sig in cross_project_signals:
        for blocker in sig.get("blockers", []):
            cross_project_risks.append(f"[{sig['title']}] {blocker}")
        for risk in sig.get("risks", []):
            cross_project_risks.append(f"[{sig['title']}] {risk}")

    # ── 15. LLM narrative synthesis (with rule-based fallback) ──────────────
    print("  🤖  Synthesising narrative with LLM...", file=sys.stderr)
    llm_narrative = _llm_synthesize_narrative(project_cards, decisions, week_end.isoformat())

    if llm_narrative:
        _apply_llm_narrative(project_cards, llm_narrative)
        top_risk = llm_narrative.get("top_risk") or _build_bottom_line(project_cards, decisions)
        this_week = _build_this_week_summary(project_cards)
        next_week_sum = _build_next_week_summary(project_cards)
        client_summary = None
    else:
        top_risk = _build_bottom_line(project_cards, decisions)
        this_week = _build_this_week_summary(project_cards)
        next_week_sum = _build_next_week_summary(project_cards)
        client_summary = None

    # ── 16. Portfolio risks ─────────────────────────────────────────────────
    print("  🔍 Building portfolio risks...", file=sys.stderr)
    portfolio_risks = _build_portfolio_risks(project_cards, inactive_group)

    # ── 17. Leadership priorities ──────────────────────────────────────────
    leadership_priorities = _build_leadership_priorities(project_cards, decisions)
    client_summary = _build_client_summary(project_cards, inactive_group)

    # ── 18. Portfolio summary ────────────────────────────────────────────────
    summary = PortfolioSummary(
        total_projects=len(project_cards),
        on_track=sum(1 for c in project_cards if c.status == "on_track"),
        at_risk=sum(1 for c in project_cards if c.status == "at_risk"),
        off_track=sum(1 for c in project_cards if c.status == "off_track"),
        inactive=sum(1 for c in project_cards if c.is_inactive),
        decisions_needed=len(decisions),
        top_risk=top_risk,
        portfolio_risks=portfolio_risks,
        leadership_priorities=leadership_priorities,
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
        this_week_summary=this_week,
        next_week_summary=next_week_sum,
        client_summary=client_summary,
        inactive_group=inactive_group,
        score_methodology=_SCORE_METHODOLOGY,
        sources=sources,
        errors=errors,
    )

    # ── 15. Render ──────────────────────────────────────────────────────────
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

    recipients: list = cfg_get("steering.recipients") or cfg_get("email.recipients", []) or []
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
            local_gmail_path = Path(__file__).parent / "google_api.py"
            if local_gmail_path.exists():
                gmail_path = local_gmail_path
                print(f"ℹ️  Gmail script not found at configured path, using local helper {gmail_path}",
                      file=sys.stderr)
            else:
                print(f"⚠️  Gmail script not found at {gmail_path} — skipping email", file=sys.stderr)
                gmail_path = None
        if gmail_path:
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
