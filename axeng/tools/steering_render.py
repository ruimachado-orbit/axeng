#!/usr/bin/env python3
"""
Steering Report — HTML + Markdown Renderer
Pure Python, no template engine. Brand colors are read from config
(steering.brand.*) with Maio Labs defaults.

Main entries:
  render_html(report: SteeringReport) -> str
  render_markdown(report: SteeringReport) -> str
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.steering_schema import ProjectCard, SteeringReport


# ── Brand tokens (overridable via config steering.brand.*) ───────────────────

def _brand() -> dict:
    try:
        from config import get
        b = get("steering.brand", {}) or {}
    except Exception:
        b = {}
    return {
        "BG":          b.get("background",  "#faf9f6"),
        "NAVY":        b.get("primary",      "#1a1a2e"),
        "ACCENT":      b.get("accent",       "#7c8cff"),
        "CARD":        b.get("card",         "#f0eeea"),
        "BORDER":      b.get("border",       "#e8e5df"),
        "BORDER_DARK": b.get("border_dark",  "#e0ddd6"),
        "MUTED":       b.get("muted",        "#888888"),
        "TEXT":        b.get("text",         "#333333"),
        "WHITE":       "#ffffff",
        "DANGER":      b.get("danger",       "#e05a5a"),
        "WARNING":     b.get("warning",      "#d97706"),
        "SUCCESS":     b.get("success",      "#22c55e"),
        "FONT":        b.get("font",         "Gelasio, Georgia, 'Times New Roman', serif"),
        "FONT_UI":     "-apple-system, 'Helvetica Neue', Arial, sans-serif",
        "COMPANY":     b.get("company",      "Maio Labs"),
        "TAGLINE":     b.get("tagline",      "Build · Govern · Own Your AI Layer"),
        "LOCATION":    b.get("location",     "Lisbon"),
    }


# ── Colour helpers ────────────────────────────────────────────────────────────

def _status_color(status: str, t: dict) -> str:
    return {"off_track": t["DANGER"], "at_risk": t["WARNING"]}.get(status, t["SUCCESS"])

def _status_label(status: str) -> str:
    return {"off_track": "Off Track", "at_risk": "At Risk"}.get(status, "On Track")

def _eta_label(eta: str) -> str:
    return {"critical": "Critical", "high": "High", "medium": "Medium"}.get(eta, "Low")

def _eta_color(eta: str, t: dict) -> str:
    return {"critical": t["DANGER"], "high": t["DANGER"], "medium": t["WARNING"]}.get(eta, t["SUCCESS"])


# ── HTML primitives ───────────────────────────────────────────────────────────

def _row(content: str) -> str:
    return f"<tr><td>{content}</td></tr>\n"

def _section_label(text: str, t: dict) -> str:
    return (
        f'<p style="margin:0 0 10px;font-family:{t["FONT_UI"]};font-size:10px;'
        f'font-weight:600;color:{t["NAVY"]};text-transform:uppercase;letter-spacing:0.1em;">'
        f"{text}</p>"
    )

def _card_table(rows_html: str, t: dict) -> str:
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border:1px solid {t["BORDER_DARK"]};border-radius:6px;'
        f'background:{t["WHITE"]};overflow:hidden;">'
        f"{rows_html}</table>"
    )


# ── Section builders ──────────────────────────────────────────────────────────

def _html_header(report: SteeringReport, recipient: str, week_label: str, t: dict) -> str:
    return (
        f'<tr><td style="background:{t["NAVY"]};border-radius:8px 8px 0 0;padding:32px 32px 28px;">'
        f'<p style="margin:0 0 16px;font-family:{t["FONT_UI"]};font-size:11px;'
        f'letter-spacing:6px;text-transform:uppercase;color:rgba(255,255,255,0.5);">'
        f'{t["COMPANY"]}</p>'
        f'<h1 style="margin:0 0 6px;font-family:{t["FONT"]};font-size:26px;font-weight:400;'
        f'color:{t["WHITE"]};letter-spacing:-0.02em;line-height:1.2;">Steering Report</h1>'
        f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:12px;color:rgba(255,255,255,0.5);">'
        f'{week_label} &nbsp;·&nbsp; For {recipient} &nbsp;·&nbsp; {report.generated_at[:10]}'
        f'</p></td></tr>\n'
    )


def _html_bottom_line(text: str, t: dict) -> str:
    return (
        f'<tr><td style="padding:0;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td width="4" style="background:{t["ACCENT"]};"></td>'
        f'<td style="background:{t["CARD"]};padding:20px 24px;">'
        f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
        f'color:{t["ACCENT"]};text-transform:uppercase;letter-spacing:0.1em;">Bottom Line</p>'
        f'<p style="margin:0;font-family:{t["FONT"]};font-size:16px;line-height:1.6;color:{t["NAVY"]};">'
        f'{text}</p>'
        f'</td></tr></table></td></tr>\n'
    )


def _html_sprint_pulse(sp, t: dict) -> str:
    if not sp or not sp.get("sprint_name"):
        return ""
    days_left = sp.get("days_remaining_in_sprint")
    days_str = ""
    if days_left is not None:
        color = "rgba(224,90,90,0.9)" if days_left <= 2 else "rgba(255,255,255,0.8)"
        days_str = f' &nbsp;·&nbsp; <span style="color:{color};">{days_left}d left</span>'

    trend = sp.get("velocity_trend", "stable")
    trend_html = {
        "declining": f'<span style="color:{t["DANGER"]};font-weight:600;">↓ Declining</span>',
        "improving": f'<span style="color:{t["SUCCESS"]};font-weight:600;">↑ Improving</span>',
        "stable":    f'<span style="color:{t["MUTED"]};">→ Stable</span>',
    }.get(trend, f'<span style="color:{t["MUTED"]};">— Insufficient data</span>')

    sprint_status = sp.get("sprint_status", "unknown")
    status_dot = {
        "on_track":  f'<span style="color:{t["SUCCESS"]};">● On track</span>',
        "at_risk":   f'<span style="color:{t["WARNING"]};">● At risk</span>',
        "off_track": f'<span style="color:{t["DANGER"]};">● Off track</span>',
    }.get(sprint_status, "")

    return (
        f'<tr><td style="padding:24px 0 0;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border:1px solid {t["BORDER_DARK"]};border-radius:6px;background:{t["WHITE"]};">'
        f'<tr><td style="padding:12px 20px;border-bottom:1px solid {t["BORDER"]};'
        f'background:{t["NAVY"]};border-radius:6px 6px 0 0;">'
        f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.6);">'
        f'Sprint Pulse &nbsp;·&nbsp; {sp["sprint_name"]}{days_str}</p></td></tr>'
        f'<tr><td style="padding:14px 20px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="font-family:{t["FONT_UI"]};font-size:12px;"><tr>'
        f'<td style="width:50%;vertical-align:top;color:{t["TEXT"]};">'
        f'<span style="color:{t["MUTED"]};text-transform:uppercase;font-size:10px;'
        f'letter-spacing:0.08em;">Sprint</span><br>'
        f'<strong style="font-size:14px;color:{t["NAVY"]};">'
        f'{int(sp.get("sprint_completion_rate", 0))}% done</strong>'
        f' &nbsp;/&nbsp; {int(sp.get("sprint_time_progress", 0))}% elapsed'
        f' &nbsp; {status_dot}</td>'
        f'<td style="width:50%;vertical-align:top;padding-left:20px;'
        f'border-left:1px solid {t["BORDER"]};color:{t["TEXT"]};">'
        f'<span style="color:{t["MUTED"]};text-transform:uppercase;font-size:10px;'
        f'letter-spacing:0.08em;">Team Velocity · last {sp.get("cycles_analyzed", 0)} sprints</span><br>'
        f'<strong style="font-size:14px;color:{t["NAVY"]};">{sp.get("velocity_avg", 0)} pts/day</strong>'
        f' &nbsp; {trend_html}'
        f'</td></tr></table></td></tr></table></td></tr>\n'
    )


def _html_decisions(decisions: list[dict], t: dict) -> str:
    if not decisions:
        return ""
    rows = ""
    for i, d in enumerate(decisions):
        border = f'border-bottom:1px solid {t["BORDER"]};' if i < len(decisions) - 1 else ""
        col = _status_color(d.get("status", "on_track"), t)
        rows += (
            f'<tr style="{border}"><td style="padding:14px 20px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td width="12" style="vertical-align:top;padding-top:3px;">'
            f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
            f'background:{col};margin-right:10px;"></span></td>'
            f'<td><p style="margin:0 0 2px;font-family:{t["FONT_UI"]};font-size:13px;'
            f'font-weight:600;color:{t["NAVY"]};">{d.get("project","")}'
            f'<span style="font-weight:400;color:{t["MUTED"]};font-size:11px;margin-left:8px;">'
            f'{d.get("owner","")}</span></p>'
            f'<p style="margin:0;font-family:{t["FONT"]};font-size:13px;'
            f'color:{t["TEXT"]};line-height:1.5;">{d.get("text","")}</p>'
            f'</td></tr></table></td></tr>\n'
        )
    return (
        f'<tr><td style="padding:24px 0 0;">'
        f'{_section_label(f"Decisions Needed This Week", t)}'
        f'{_card_table(rows, t)}'
        f'</td></tr>\n'
    )


def _html_portfolio_table(projects: list, t: dict) -> str:
    header = (
        f'<tr style="background:{t["NAVY"]};">'
        + "".join(
            f'<td style="padding:8px 12px;color:rgba(255,255,255,0.6);font-size:10px;'
            f'text-transform:uppercase;letter-spacing:0.08em;">{col}</td>'
            for col in ["Project", "Owner", "Progress", "Status", "Target"]
        )
        + "</tr>\n"
    )
    rows = ""
    for p in projects:
        work = int(p.get("work_progress_pct", 0))
        time = int(p.get("time_progress_pct", 0))
        col = _status_color(p.get("status", "on_track"), t)

        # Progress bar (160px wide)
        filled_w = min(int(work * 1.6), 160)
        empty_w = 160 - filled_w
        bar = (
            f'<table width="160" cellpadding="0" cellspacing="0" border="0" '
            f'style="display:inline-table;border-radius:3px;overflow:hidden;"><tr>'
            + (f'<td width="{filled_w}" height="6" style="background:{col};"></td>' if work > 0 else "")
            + (f'<td height="6" style="background:{t["BORDER_DARK"]};"></td>' if work < 100 else "")
            + f'</tr></table>'
        )
        # Time cursor
        cursor_w = min(int(time * 1.6), 158)
        cursor = (
            f'<table width="160" cellpadding="0" cellspacing="0" border="0" '
            f'style="display:inline-table;margin-top:1px;"><tr>'
            f'<td width="{cursor_w}" height="2" style="background:transparent;"></td>'
            f'<td width="2" height="2" style="background:{t["MUTED"]};"></td>'
            f'<td height="2" style="background:transparent;"></td>'
            f'</tr></table>'
        )
        status_badge = (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;'
            f'font-size:10px;font-weight:600;color:{t["WHITE"]};background:{col};">'
            f'{_status_label(p.get("status","on_track"))}</span>'
        )
        target_date = p.get("target_date") or "—"
        days_left = p.get("days_left")
        days_html = ""
        if days_left is not None:
            day_color = t["DANGER"] if days_left < 14 else t["MUTED"]
            days_html = f'<br><span style="color:{day_color};">{days_left}d</span>'

        rows += (
            f'<tr style="border-top:1px solid {t["BORDER"]};">'
            f'<td style="padding:10px 12px;font-weight:600;color:{t["NAVY"]};font-size:13px;">{p.get("name","")}</td>'
            f'<td style="padding:10px 12px;color:{t["MUTED"]};font-size:12px;">{p.get("owner","")}</td>'
            f'<td style="padding:10px 12px;">{bar}{cursor}'
            f'<span style="font-size:10px;color:{t["MUTED"]};margin-left:6px;">{work}%</span></td>'
            f'<td style="padding:10px 12px;">{status_badge}</td>'
            f'<td style="padding:10px 12px;font-size:11px;color:{t["MUTED"]};white-space:nowrap;">'
            f'{target_date}{days_html}</td>'
            f'</tr>\n'
        )
    return (
        f'<tr><td style="padding:24px 0 0;">'
        f'{_section_label(f"Portfolio — {len(projects)} Projects", t)}'
        f'{_card_table(header + rows, t)}'
        f'</td></tr>\n'
    )


def _html_project_card(p: dict, sp_trend: str, t: dict) -> str:
    col = _status_color(p.get("status", "on_track"), t)
    work = int(p.get("work_progress_pct", 0))
    time_pct = int(p.get("time_progress_pct", 0))
    eta = p.get("eta_risk", "low")

    vel_html = ""
    if sp_trend == "declining":
        vel_html = f' &nbsp;·&nbsp; <span style="color:{t["DANGER"]};">↓ team vel</span>'
    elif sp_trend == "improving":
        vel_html = f' &nbsp;·&nbsp; <span style="color:{t["SUCCESS"]};">↑ team vel</span>'

    target = p.get("target_date", "")
    days_left = p.get("days_left")
    target_str = target if target else "No target date"
    if target and days_left is not None:
        target_str += f" ({days_left}d left)"

    # Milestones — show next upcoming one
    milestones = p.get("milestones") or []
    from datetime import date as _date
    today_str = _date.today().isoformat()
    upcoming = [m for m in milestones if m.get("target_date", "") >= today_str]
    upcoming.sort(key=lambda m: m.get("target_date", ""))
    next_milestone = upcoming[0] if upcoming else None

    # Header
    html = (
        f'<tr><td style="padding:0 0 10px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border:1px solid {t["BORDER_DARK"]};border-radius:6px;'
        f'background:{t["WHITE"]};overflow:hidden;">'
        # colour bar + navy header
        f'<tr><td width="4" style="background:{col};"></td>'
        f'<td style="padding:12px 16px;background:{t["NAVY"]};">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td><span style="font-family:{t["FONT"]};font-size:15px;font-weight:600;'
        f'color:{t["WHITE"]};">{p.get("name","")}</span>'
        f'<span style="font-family:{t["FONT_UI"]};font-size:11px;'
        f'color:rgba(255,255,255,0.5);margin-left:10px;">{p.get("owner","")}</span></td>'
        f'<td align="right">'
        f'<span style="font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
        f'letter-spacing:0.06em;color:{col};">{_status_label(p.get("status","on_track")).upper()}</span>'
        f'<span style="font-family:{t["FONT_UI"]};font-size:10px;'
        f'color:rgba(255,255,255,0.4);margin-left:8px;">'
        f'{int(p.get("health_score",0))}/100</span>'
        f'</td></tr></table></td></tr>'
        # timeline row
        f'<tr><td width="4" style="background:{t["BORDER"]};"></td>'
        f'<td style="padding:10px 16px;border-bottom:1px solid {t["BORDER"]};background:{t["CARD"]};">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="font-family:{t["FONT_UI"]};font-size:11px;color:{t["MUTED"]};"><tr>'
        f'<td><strong style="color:{t["NAVY"]};">{work}%</strong> done'
        f' &nbsp;/&nbsp; {time_pct}% elapsed'
        f' &nbsp;·&nbsp; ETA: <span style="color:{_eta_color(eta, t)};font-weight:600;">'
        f'{_eta_label(eta)}</span>{vel_html}</td>'
        f'<td align="right">{target_str}'
        + (
            f'<br><span style="color:{t["ACCENT"]};font-size:10px;">▸ {next_milestone["name"]} · {next_milestone["target_date"]}</span>'
            if next_milestone else ""
        )
        + f'</td>'
        f'</tr></table></td></tr>'
    )

    # Blockers
    blockers = p.get("blockers", [])
    if blockers:
        items = "".join(
            f'<p style="margin:0 0 3px;font-family:{t["FONT"]};font-size:13px;'
            f'color:{t["TEXT"]};line-height:1.4;">&bull; {b}</p>'
            for b in blockers[:3]
        )
        html += (
            f'<tr><td width="4" style="background:{t["BORDER"]};"></td>'
            f'<td style="padding:10px 16px;border-bottom:1px solid {t["BORDER"]};">'
            f'<p style="margin:0 0 5px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
            f'color:{t["MUTED"]};text-transform:uppercase;letter-spacing:0.08em;">Blockers</p>'
            f'{items}</td></tr>'
        )

    # Meeting signal
    meeting = p.get("meeting_signal")
    if meeting:
        html += (
            f'<tr><td width="4" style="background:{t["ACCENT"]};"></td>'
            f'<td style="padding:10px 16px;border-bottom:1px solid {t["BORDER"]};background:#f5f4ff;">'
            f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
            f'color:{t["ACCENT"]};text-transform:uppercase;letter-spacing:0.08em;">From Meetings</p>'
            f'<p style="margin:0;font-family:{t["FONT"]};font-size:13px;'
            f'color:{t["TEXT"]};font-style:italic;line-height:1.4;">{meeting}</p>'
            f'</td></tr>'
        )

    # This week — synthesised summary from week_delta
    delta = p.get("week_delta")
    if delta:
        decision = p.get("decision_needed")
        border = f'border-bottom:1px solid {t["BORDER"]};' if decision else ""
        html += (
            f'<tr><td width="4" style="background:{t["BORDER"]};"></td>'
            f'<td style="padding:10px 16px;{border}">'
            f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
            f'color:{t["MUTED"]};text-transform:uppercase;letter-spacing:0.08em;">This Week</p>'
            f'<p style="margin:0;font-family:{t["FONT"]};font-size:13px;'
            f'color:{t["TEXT"]};line-height:1.6;">{delta}</p>'
            f'</td></tr>'
        )

    # Decision
    decision = p.get("decision_needed")
    if decision:
        html += (
            f'<tr><td width="4" style="background:{t["ACCENT"]};"></td>'
            f'<td style="padding:10px 16px;background:#f5f4ff;">'
            f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
            f'color:{t["ACCENT"]};text-transform:uppercase;letter-spacing:0.08em;">Action Needed</p>'
            f'<p style="margin:0;font-family:{t["FONT"]};font-size:13px;'
            f'font-weight:600;color:{t["NAVY"]};line-height:1.4;">{decision}</p>'
            f'</td></tr>'
        )

    html += f'</table></td></tr>\n'
    return html


def _html_cross_project(risks: list[str], t: dict) -> str:
    if not risks:
        return ""
    items = "".join(
        f'<p style="margin:0 0 5px;font-family:{t["FONT"]};font-size:13px;'
        f'color:{t["TEXT"]};line-height:1.5;">&bull; {r}</p>'
        for r in risks
    )
    return (
        f'<tr><td style="padding:8px 0 0;">'
        f'{_section_label("Cross-Project Signals", t)}'
        f'{_card_table(f"<tr><td style=padding:14px;>{items}</td></tr>", t)}'
        f'</td></tr>\n'
    )


def _html_capacity(ooo: list[str], t: dict) -> str:
    if not ooo:
        return ""
    return (
        f'<tr><td style="padding:16px 0 0;">'
        f'{_section_label("Team Capacity", t)}'
        f'{_card_table(f"<tr><td style=padding:12px 16px;font-family:{t[chr(39)]}FONT_UI{chr(39)};font-size:13px;color:{t[chr(39)]}TEXT{chr(39)};>Out of office: <strong style=color:{t[chr(39)]}NAVY{chr(39)};>{chr(44).join(ooo)}</strong></td></tr>", t)}'
        f'</td></tr>\n'
    )


def _html_footer(sources: list[str], errors: list[str], t: dict) -> str:
    errors_html = ""
    if errors:
        errors_html = (
            f' &nbsp;·&nbsp; <span style="color:{t["WARNING"]};">partial data</span>'
        )
    return (
        f'<tr><td style="padding:32px 0 0;border-top:1px solid {t["BORDER"]};">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td><p style="margin:0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["MUTED"]};">'
        f'<strong style="color:{t["NAVY"]};">{t["COMPANY"]}</strong>'
        f' &nbsp;·&nbsp; {t["LOCATION"]}'
        f' &nbsp;·&nbsp; {t["TAGLINE"]}</p></td>'
        f'<td align="right"><p style="margin:0;font-family:{t["FONT_UI"]};font-size:10px;'
        f'color:{t["MUTED"]};">Signals: {", ".join(sources) or "none"}{errors_html}</p></td>'
        f'</tr></table></td></tr>\n'
    )


# ── Public entry: HTML ────────────────────────────────────────────────────────

def render_html(report: SteeringReport) -> str:
    """Render the steering report as email-safe HTML. No external dependencies."""
    t = _brand()

    try:
        end = datetime.fromisoformat(report.week_end)
        week_label = f"Week of {end.strftime('%-d %B %Y')}"
    except Exception:
        week_label = f"Week of {report.week_end}"

    try:
        from config import get as cfg_get
        recipients = cfg_get("steering.recipients", []) or []
        raw = recipients[0] if recipients else ""
        if "<" in raw:
            recipient = raw.split("<")[0].strip()
        elif "@" in raw:
            recipient = "Recipient"
        else:
            recipient = raw or "Recipient"
    except Exception:
        recipient = "Recipient"

    # Serialise for section builders
    from tools.steering_schema import report_to_dict
    d = report_to_dict(report)
    projects = d.get("projects", [])
    sp = d.get("sprint_signals") or {}
    sp_trend = sp.get("velocity_trend", "stable")

    rows = ""
    rows += _html_header(report, recipient, week_label, t)
    rows += _html_bottom_line(report.portfolio_summary.top_risk or "No summary.", t)
    rows += _html_sprint_pulse(sp, t)
    rows += _html_decisions(d.get("decisions_needed", []), t)
    rows += _html_portfolio_table(projects, t)

    # Project cards section label
    rows += (
        f'<tr><td style="padding:24px 0 0;">'
        f'{_section_label("Project Detail", t)}'
        f'</td></tr>\n'
    )
    for p in projects:
        rows += _html_project_card(p, sp_trend, t)

    rows += _html_cross_project(d.get("cross_project_risks", []), t)

    # Capacity — build inline to avoid f-string quoting issues
    ooo = (d.get("capacity_signals") or {}).get("ooo_this_week", [])
    if ooo:
        names = ", ".join(ooo)
        rows += (
            f'<tr><td style="padding:16px 0 0;">'
            f'{_section_label("Team Capacity", t)}'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="border:1px solid {t["BORDER_DARK"]};border-radius:6px;background:{t["WHITE"]};">'
            f'<tr><td style="padding:12px 16px;font-family:{t["FONT_UI"]};font-size:13px;'
            f'color:{t["TEXT"]};">Out of office: '
            f'<strong style="color:{t["NAVY"]};">{names}</strong></td></tr>'
            f'</table></td></tr>\n'
        )

    rows += _html_footer(report.sources, report.errors, t)

    return (
        f'<!DOCTYPE html><html lang="en"><head>'
        f'<meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f'<title>Steering Report — {week_label}</title>'
        f'</head>'
        f'<body style="margin:0;padding:0;background:{t["BG"]};'
        f'font-family:{t["FONT"]};color:{t["TEXT"]};">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:{t["BG"]};padding:40px 0 64px;">'
        f'<tr><td align="center">'
        f'<table width="660px" cellpadding="0" cellspacing="0" border="0" '
        f'style="max-width:660px;width:100%;">'
        f'{rows}'
        f'</table></td></tr></table>'
        f'</body></html>'
    )


# ── Public entry: Markdown ────────────────────────────────────────────────────

def render_markdown(report: SteeringReport) -> str:
    """Render the steering report as plain Markdown for CLI/Telegram output."""
    lines: list[str] = []
    s = report.portfolio_summary

    lines.append(f"# Steering Report — {report.week_end}")
    lines.append(f"*{report.week_start} → {report.week_end} · generated {report.generated_at[:16].replace('T', ' ')}*")
    lines.append("")
    lines.append(f"> **{s.top_risk}**")
    lines.append("")

    sp = report.sprint_signals
    if sp and sp.sprint_name:
        trend_icon = {"declining": "↓", "improving": "↑", "stable": "→"}.get(sp.velocity_trend, "—")
        days_str = f" · {sp.days_remaining_in_sprint}d left" if sp.days_remaining_in_sprint is not None else ""
        lines.append("## Sprint Pulse")
        lines.append("")
        lines.append(
            f"**{sp.sprint_name}**{days_str} · "
            f"{int(sp.sprint_completion_rate)}% done / {int(sp.sprint_time_progress)}% elapsed · "
            f"{sp.sprint_status.replace('_', ' ').title()}"
        )
        lines.append(
            f"Team velocity: **{sp.velocity_avg} pts/day** avg "
            f"(last {sp.cycles_analyzed} sprints) {trend_icon} {sp.velocity_trend.replace('_', ' ').title()}"
        )
        lines.append("")

    if report.decisions_needed:
        lines.append(f"## Decisions Needed ({len(report.decisions_needed)})")
        lines.append("")
        for d in report.decisions_needed:
            icon = {"on_track": "🟢", "at_risk": "🟡", "off_track": "🔴"}.get(d["status"], "⚪")
            lines.append(f"- {icon} **{d['project']}** ({d['owner']}): {d['text']}")
        lines.append("")

    lines.append(f"## Portfolio ({s.total_projects} projects)")
    lines.append("")
    lines.append("| Project | Owner | Progress | Status | Target | Days |")
    lines.append("|---------|-------|----------|--------|--------|------|")
    N = 20
    for p in report.projects:
        work = int(p.work_progress_pct)
        time = int(p.time_progress_pct)
        filled = round(work * N / 100)
        cursor = min(round(time * N / 100), N - 1)
        bar = list("█" * filled + "░" * (N - filled))
        bar[cursor] = "↑"
        icon = {"on_track": "🟢", "at_risk": "🟡", "off_track": "🔴"}.get(p.status, "⚪")
        lines.append(
            f"| {p.name} | {p.owner} | `{''.join(bar)}` {work}% "
            f"| {icon} {p.status.replace('_',' ').title()} "
            f"| {p.target_date or '—'} | {p.days_left if p.days_left is not None else '—'} |"
        )
    lines.append("")

    lines.append("## Project Detail")
    lines.append("")
    for p in report.projects:
        icon = {"on_track": "🟢", "at_risk": "🟡", "off_track": "🔴"}.get(p.status, "⚪")
        lines.append(f"### {icon} {p.name} — {p.owner}")
        lines.append("")
        lines.append(
            f"**Timeline:** {int(p.work_progress_pct)}% done / {int(p.time_progress_pct)}% elapsed"
            + (f" · **{p.days_left}d left**" if p.days_left is not None else "")
            + (f" · target {p.target_date}" if p.target_date else "")
        )
        lines.append(f"**ETA:** {p.eta_risk.upper()} · **Score:** {int(p.health_score)}/100")
        if p.milestones:
            today_str = str(__import__('datetime').date.today())
            upcoming = sorted([m for m in p.milestones if m.get("target_date","") >= today_str], key=lambda m: m.get("target_date",""))
            if upcoming:
                m = upcoming[0]
                lines.append(f"**Next milestone:** {m['name']} — {m['target_date']}")
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

    if report.cross_project_risks:
        lines.append("## Cross-Project Signals")
        lines.append("")
        for r in report.cross_project_risks:
            lines.append(f"- {r}")
        lines.append("")

    if report.capacity_signals.ooo_this_week:
        lines.append("## Team Capacity")
        lines.append("")
        lines.append(f"OOO: {', '.join(report.capacity_signals.ooo_this_week)}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Axeng · signals: {', '.join(report.sources) or 'none'}*")
    if report.errors:
        lines.append(f"*Partial data: {'; '.join(report.errors)}*")

    return "\n".join(lines)
