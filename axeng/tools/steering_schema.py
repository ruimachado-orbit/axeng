#!/usr/bin/env python3
"""
CEO Steering Report — Schema
Defines the data contract for the weekly executive document.
All other steering modules produce and consume these dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal


# ── Status / confidence types ────────────────────────────────────────────────

Status = Literal["on_track", "at_risk", "off_track"]
Confidence = Literal["high", "medium", "low"]
Forecast = Literal[
    "delivering_as_planned",
    "target_date_at_risk",
    "blocked_needs_escalation",
    "unowned_assign_now",
]
EtaRisk = Literal["low", "medium", "high", "critical"]
TimelinePosition = Literal["ahead", "on_plan", "behind", "significantly_behind"]


# ── Granola / transcript ─────────────────────────────────────────────────────

@dataclass
class TranscriptSignal:
    note_id: str
    title: str
    note_date: str                        # ISO date
    url: str | None = None
    decisions: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    commitments: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    confidence_tone: Literal["positive", "neutral", "concerned", "urgent"] = "neutral"


# ── GitHub Issues ────────────────────────────────────────────────────────────

@dataclass
class IssueSignals:
    stale_count: int = 0          # open, not updated in N days
    unowned_count: int = 0        # open, no assignee
    overdue_count: int = 0        # past milestone / target date
    backlog_growth: int = 0       # created_this_week − closed_this_week
    blocked_threads: int = 0      # body/comments contain blocker keywords
    top_stale: list[str] = field(default_factory=list)    # ["org/repo#12 — title", ...]
    top_blocked: list[str] = field(default_factory=list)
    risk_score: float = 0.0       # 0–100, higher = more risk


# ── Linear ───────────────────────────────────────────────────────────────────

@dataclass
class SprintSignals:
    """Current sprint position — cadence differs from weekly steering (2-week sprint vs weekly report)."""
    sprint_name: str | None = None
    sprint_ends_at: str | None = None          # ISO datetime
    days_remaining_in_sprint: int | None = None
    sprint_completion_rate: float = 0.0        # % of sprint issues done
    sprint_time_progress: float = 0.0          # % of sprint calendar elapsed
    sprint_status: str = "unknown"             # on_track / at_risk / off_track / unknown
    velocity_trend: str = "stable"             # improving / stable / declining / insufficient_data
    velocity_avg: float = 0.0                  # pts/day, avg last 5 sprints
    velocity_current: float = 0.0             # pts/day, current sprint
    cycles_analyzed: int = 0


@dataclass
class LinearSignals:
    completion_rate: float = 0.0  # 0–100 project-level
    staleness_rate: float = 0.0   # 0–100
    velocity: float = 0.0         # issues/day
    in_progress: int = 0
    todo: int = 0
    completed: int = 0
    top_stale_issues: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


# ── Evidence item ────────────────────────────────────────────────────────────

@dataclass
class Evidence:
    source: Literal["linear", "github_issues", "granola", "risk_radar", "sprint"]
    text: str
    ref: str | None = None        # issue ID, note ID, PR number, etc.
    severity: Literal["info", "warning", "critical"] = "info"


# ── Per-project card ─────────────────────────────────────────────────────────

@dataclass
class ProjectCard:
    # Identity
    name: str
    owner: str
    linear_project_id: str | None = None
    repos: list[str] = field(default_factory=list)

    # Status
    status: Status = "on_track"
    health_score: float = 0.0     # 0–100
    confidence: Confidence = "medium"
    forecast: Forecast = "delivering_as_planned"

    # Timeline
    target_date: str | None = None       # ISO date
    start_date: str | None = None        # ISO date
    days_left: int | None = None
    time_progress_pct: float = 0.0       # % of calendar time elapsed
    work_progress_pct: float = 0.0       # % of issues completed
    timeline_position: TimelinePosition = "on_plan"
    eta_risk: EtaRisk = "low"

    # Signals
    linear_signals: LinearSignals = field(default_factory=LinearSignals)
    issue_signals: IssueSignals = field(default_factory=IssueSignals)
    transcript_signals: list[TranscriptSignal] = field(default_factory=list)

    # CEO-facing outputs
    blockers: list[str] = field(default_factory=list)
    wins: list[str] = field(default_factory=list)
    week_delta: str | None = None         # "2 issues closed, 5 opened — backlog growing"
    decision_needed: str | None = None    # null = no action needed from CEO
    meeting_signal: str | None = None     # one-liner from latest relevant Granola note

    # Traceability
    evidence: list[Evidence] = field(default_factory=list)


# ── Cross-project ─────────────────────────────────────────────────────────────

@dataclass
class CapacitySignals:
    ooo_this_week: list[str] = field(default_factory=list)
    overloaded_members: list[str] = field(default_factory=list)


@dataclass
class PortfolioSummary:
    total_projects: int = 0
    on_track: int = 0
    at_risk: int = 0
    off_track: int = 0
    decisions_needed: int = 0
    top_risk: str | None = None           # one-sentence bottom line


# ── Top-level report ─────────────────────────────────────────────────────────

@dataclass
class SteeringReport:
    report_id: str                         # "steering-2026-05-30"
    generated_at: str                      # ISO datetime
    week_start: str                        # ISO date  (Monday)
    week_end: str                          # ISO date  (Friday)

    portfolio_summary: PortfolioSummary = field(default_factory=PortfolioSummary)
    projects: list[ProjectCard] = field(default_factory=list)
    decisions_needed: list[dict] = field(default_factory=list)   # [{project, text, action}]
    cross_project_risks: list[str] = field(default_factory=list)
    capacity_signals: CapacitySignals = field(default_factory=CapacitySignals)

    sprint_signals: SprintSignals = field(default_factory=SprintSignals)

    sources: list[str] = field(default_factory=list)  # which signals were available
    errors: list[str] = field(default_factory=list)   # non-fatal collection failures

    # Rendered outputs (populated in Phase 5)
    rendered_html: str | None = None
    rendered_markdown: str | None = None


# ── Serialisation helpers ────────────────────────────────────────────────────

def _to_dict(obj) -> object:
    """Recursively convert dataclasses to plain dicts for JSON serialisation."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_dict(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_to_dict(i) for i in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def report_to_dict(report: SteeringReport) -> dict:
    """Serialise a SteeringReport to a JSON-safe dict."""
    return _to_dict(report)
