#!/usr/bin/env python3
"""
Steering Report — HTML + Markdown Renderer
Loads the Jinja2 template (user copy first, default fallback) and renders
the SteeringReport into email-safe HTML and plain Markdown.

Main entries:
  render_html(report: SteeringReport) -> str
  render_markdown(report: SteeringReport) -> str
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.steering_schema import SteeringReport, report_to_dict

# ── Template loading ─────────────────────────────────────────────────────────

_TEMPLATE_NAME = "steering-email.html.j2"
_DEFAULT_TEMPLATE = Path(__file__).parent.parent / "templates" / _TEMPLATE_NAME
_USER_TEMPLATE = Path.home() / ".axeng" / "templates" / _TEMPLATE_NAME


def _load_template_string() -> str:
    """Return user template if it exists, otherwise ship the default."""
    path = _USER_TEMPLATE if _USER_TEMPLATE.exists() else _DEFAULT_TEMPLATE
    return path.read_text(encoding="utf-8")


def _build_template_context(report: SteeringReport) -> dict:
    """
    Convert SteeringReport into the flat dict the Jinja2 template expects.
    Uses report_to_dict for full serialisation, then adds convenience fields.
    """
    d = report_to_dict(report)

    # Week label e.g. "Week of 26 May 2026"
    try:
        end = datetime.fromisoformat(report.week_end)
        d["week_label"] = f"Week of {end.strftime('%-d %B %Y')}"
    except Exception:
        d["week_label"] = f"Week of {report.week_end}"

    # Recipient name from first configured recipient (display only)
    from config import get as cfg_get
    recipients: list = cfg_get("steering.recipients", [])
    if recipients:
        raw = recipients[0]
        # "John Doe <john@co.com>" → "John Doe", "john@co.com" → "Recipient"
        if "<" in raw:
            d["recipient_name"] = raw.split("<")[0].strip()
        elif "@" in raw:
            d["recipient_name"] = "Recipient"
        else:
            d["recipient_name"] = raw
    else:
        d["recipient_name"] = "Recipient"

    # OOO list (flat names)
    d["ooo"] = report.capacity_signals.ooo_this_week

    # Bottom line from portfolio summary
    d["bottom_line"] = report.portfolio_summary.top_risk or "No summary available."

    # Flatten project cards — add convenience colour/label fields
    for p in d.get("projects", []):
        status = p.get("status", "on_track")
        p["status_label"] = {"on_track": "On Track", "at_risk": "At Risk",
                              "off_track": "Off Track"}.get(status, status.replace("_", " ").title())
        p["status_color"] = {"on_track": "#16a34a", "at_risk": "#d97706",
                              "off_track": "#dc2626"}.get(status, "#6b7280")
        # Flatten nested signal dicts for easier template access
        p["work_progress_pct"] = p.get("work_progress_pct", 0)
        p["time_progress_pct"] = p.get("time_progress_pct", 0)

    return d


def render_html(report: SteeringReport) -> str:
    """Render the steering report as email-safe HTML via the Jinja2 template."""
    try:
        from jinja2 import Environment, select_autoescape
    except ImportError:
        raise RuntimeError(
            "Jinja2 is required for HTML rendering.\n"
            "Install it: pip install jinja2  (or activate the project venv)"
        )

    template_str = _load_template_string()
    env = Environment(
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    tmpl = env.from_string(template_str)
    ctx = _build_template_context(report)
    return tmpl.render(report=ctx)


# ── Markdown renderer ────────────────────────────────────────────────────────

def render_markdown(report: SteeringReport) -> str:
    """
    Render the steering report as plain Markdown.
    Used for CLI output, Telegram, and the .md archive file.
    """
    lines: list[str] = []
    s = report.portfolio_summary

    lines.append(f"# Engineering Update — {report.week_end}")
    lines.append(f"*{report.week_start} → {report.week_end} · generated {report.generated_at[:16].replace('T', ' ')}*")
    lines.append("")

    # Bottom line
    lines.append(f"> **{s.top_risk}**")
    lines.append("")

    # Sprint pulse
    sp = report.sprint_signals
    if sp and sp.sprint_name:
        trend_icon = {"declining": "↓", "improving": "↑", "stable": "→"}.get(
            sp.velocity_trend, "—"
        )
        trend_label = sp.velocity_trend.replace("_", " ").title()
        days_left_str = f" · {sp.days_remaining_in_sprint}d left" if sp.days_remaining_in_sprint is not None else ""
        lines.append("## Sprint Pulse")
        lines.append("")
        lines.append(
            f"**{sp.sprint_name}**{days_left_str} · "
            f"{int(sp.sprint_completion_rate)}% done / {int(sp.sprint_time_progress)}% elapsed · "
            f"{sp.sprint_status.replace('_', ' ').title()}"
        )
        lines.append(
            f"Team velocity: **{sp.velocity_avg} pts/day** avg (last {sp.cycles_analyzed} sprints) "
            f"{trend_icon} {trend_label}"
        )
        lines.append("")

    # Decisions
    if report.decisions_needed:
        lines.append(f"## Decisions Needed ({len(report.decisions_needed)})")
        lines.append("")
        for d in report.decisions_needed:
            status_icon = {"on_track": "🟢", "at_risk": "🟡", "off_track": "🔴"}.get(d["status"], "⚪")
            lines.append(f"- {status_icon} **{d['project']}** ({d['owner']}): {d['text']}")
        lines.append("")

    # Portfolio table
    lines.append(f"## Portfolio ({s.total_projects} projects)")
    lines.append("")
    lines.append("| Project | Owner | Progress | Status | Target | Days left |")
    lines.append("|---------|-------|----------|--------|--------|-----------|")

    _bar_chars = 20
    for p in report.projects:
        work = int(p.work_progress_pct)
        time = int(p.time_progress_pct)
        filled = round(work * _bar_chars / 100)
        # Place a cursor marker at time position
        cursor_pos = round(time * _bar_chars / 100)
        bar_list = ["█"] * filled + ["░"] * (_bar_chars - filled)
        if 0 <= cursor_pos < _bar_chars:
            bar_list[cursor_pos] = "↑"
        bar = "".join(bar_list)

        status_icon = {"on_track": "🟢", "at_risk": "🟡", "off_track": "🔴"}.get(p.status, "⚪")
        target = p.target_date or "—"
        days = str(p.days_left) if p.days_left is not None else "—"
        lines.append(
            f"| {p.name} | {p.owner} | `{bar}` {work}% | {status_icon} {p.status.replace('_', ' ').title()} | {target} | {days} |"
        )
    lines.append("")

    # Project cards
    lines.append("## Project Detail")
    lines.append("")
    for p in report.projects:
        status_icon = {"on_track": "🟢", "at_risk": "🟡", "off_track": "🔴"}.get(p.status, "⚪")
        lines.append(f"### {status_icon} {p.name} — {p.owner}")
        lines.append("")
        lines.append(
            f"**Timeline:** {int(p.work_progress_pct)}% done / {int(p.time_progress_pct)}% elapsed"
            + (f" · **{p.days_left}d left**" if p.days_left is not None else "")
            + (f" · target {p.target_date}" if p.target_date else "")
        )
        lines.append(f"**ETA risk:** {p.eta_risk.upper()} · **Score:** {int(p.health_score)}/100")
        lines.append("")

        if p.blockers:
            lines.append("**Blockers:**")
            for b in p.blockers[:3]:
                lines.append(f"- {b}")
            lines.append("")

        if p.meeting_signal:
            lines.append(f"**From meetings:** {p.meeting_signal}")
            lines.append("")

        if p.week_delta:
            lines.append(f"**This week:** {p.week_delta}")
            lines.append("")

        if p.decision_needed:
            lines.append(f"**⚡ Action needed:** {p.decision_needed}")
            lines.append("")

    # Cross-project risks
    if report.cross_project_risks:
        lines.append("## Cross-Project Signals")
        lines.append("")
        for risk in report.cross_project_risks:
            lines.append(f"- {risk}")
        lines.append("")

    # Capacity
    if report.capacity_signals.ooo_this_week:
        lines.append("## Team Capacity")
        lines.append("")
        lines.append(f"OOO this week: {', '.join(report.capacity_signals.ooo_this_week)}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Generated by Axeng · signals: {', '.join(report.sources) or 'none'}*")
    if report.errors:
        lines.append(f"*Partial data: {'; '.join(report.errors)}*")

    return "\n".join(lines)
