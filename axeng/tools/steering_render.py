#!/usr/bin/env python3
"""
Steering Report — HTML + Markdown Renderer
Design: Minimalist black/white with accent status indicators and CTA signals.
System font stack — no external typography dependencies.

Main entries:
  render_html(report: SteeringReport) -> str
  render_markdown(report: SteeringReport) -> str
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.steering_schema import ProjectCard, SteeringReport


# ── Design tokens ─────────────────────────────────────────────────────────────

def _brand() -> dict:
    try:
        from config import get
        b = get("steering.brand", {}) or {}
    except Exception:
        b = {}
    return {
        # Backgrounds
        "BG":          b.get("background",   "#ffffff"),
        "BG2":         b.get("bg2",          "#fafafa"),
        "CARD":        b.get("card",         "#ffffff"),
        "CARD_WARM":   b.get("card_warm",    "#f5f5f5"),
        # Text
        "INK":         b.get("ink",          "#000000"),
        "INK2":        b.get("ink2",         "#0a0a0a"),
        "TEXT":        b.get("text",         "#1a1a1a"),
        "MUTED":       b.get("muted",        "#555555"),
        "GHOST":       b.get("ghost",        "#888888"),
        # Accents — used sparingly: only statuses, CTAs, risk indicators
        "ACCENT":      b.get("accent",       "#000000"),
        "GREEN":       b.get("success",      "#16a34a"),
        "ORANGE":      b.get("warning",      "#d97706"),
        "RED":         b.get("danger",       "#dc2626"),
        # Borders
        "BORDER":      b.get("border",       "1px solid #d4d4d4"),
        "BORDER_MED":  b.get("border_med",   "1px solid #b0b0b0"),
        # Typography — system font stack, no Google Fonts dependency
        "FONT":        "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "FONT_UI":     "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "FONT_MONO":   "'SF Mono', 'Fira Code', 'Cascadia Code', monospace",
        # Meta
        "COMPANY":     b.get("company",      "Maio Labs"),
        "TAGLINE":     b.get("tagline",      "Build · Govern · Own Your AI Layer"),
        "LOCATION":    b.get("location",     "Lisbon"),
    }


# ── Status / label helpers ────────────────────────────────────────────────────

def _status_color(status: str, t: dict) -> str:
    return {"off_track": t["RED"], "at_risk": t["ORANGE"]}.get(status, t["GREEN"])

def _status_bg(status: str) -> str:
    return {"off_track": "#dc2626", "at_risk": "#d97706"}.get(status, "#16a34a")

def _status_border(status: str) -> str:
    return {"off_track": "1px solid #dc2626", "at_risk": "1px solid #d97706"}.get(status, "1px solid #16a34a")

def _status_label(status: str) -> str:
    return {"off_track": "Off Track", "at_risk": "At Risk"}.get(status, "On Track")

def _status_text_color(status: str) -> str:
    return "#ffffff"

def _eta_label(eta: str) -> str:
    return {"critical": "Critical", "high": "High", "medium": "Medium"}.get(eta, "Low")

def _eta_color(eta: str, t: dict) -> str:
    return {"critical": t["RED"], "high": t["RED"], "medium": t["ORANGE"]}.get(eta, t["MUTED"])

def _forecast_label(forecast: str) -> str:
    return {
        "delivering_as_planned":  "Delivering as planned",
        "target_date_at_risk":    "Target date at risk",
        "blocked_needs_escalation": "Blocked — needs escalation",
        "unowned_assign_now":     "Unowned — assign now",
    }.get(forecast, forecast.replace("_", " ").title())

def _project_state_label(state: str | None) -> str:
    return str(state).replace("_", " ").title() if state else "Unknown"

def _date_label(value: str | None) -> str:
    return value or "No target date"


# ── Shared HTML primitives ────────────────────────────────────────────────────

def _eyebrow(text: str, t: dict, color: str | None = None) -> str:
    c = color or t["MUTED"]
    return (
        f'<p style="margin:0 0 10px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
        f'color:{c};text-transform:uppercase;letter-spacing:0.12em;">{text}</p>'
    )

def _card(content: str, t: dict, padding: str = "24px", border: str | None = None) -> str:
    b = border or t["BORDER_MED"]
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:{t["CARD"]};border:{b};border-radius:8px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
        f'<tr><td style="padding:{padding};">{content}</td></tr>'
        f'</table>'
    )

def _card_warm(content: str, t: dict, padding: str = "24px") -> str:
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:{t["CARD_WARM"]};border:{t["BORDER"]};border-radius:8px;'
        f'box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
        f'<tr><td style="padding:{padding};">{content}</td></tr>'
        f'</table>'
    )

def _score_text_color(score: int) -> str:
    if score >= 75:
        return "#16a34a"
    if score >= 50:
        return "#d97706"
    return "#dc2626"

def _divider(t: dict) -> str:
    return f'<div style="height:1px;background:#e5e5e5;margin:0;"></div>'

def _pill(text: str, color: str, bg: str, border: str | None = None) -> str:
    b = border or "none"
    return (
        f'<span style="display:inline-block;box-sizing:border-box;min-width:88px;padding:4px 10px;'
        f'border-radius:6px;text-align:center;white-space:nowrap;'
        f'font-size:11px;font-weight:700;letter-spacing:0.03em;color:{color};background:{bg};'
        f'border:{b};line-height:1.4;">'
        f'{text}</span>'
    )

def _progress_bar(work_pct: int, time_pct: int, color: str, t: dict) -> str:
    return (
        f'<div style="position:relative;height:4px;background:#e5e5e5;border-radius:2px;overflow:visible;">'
        f'<div style="position:absolute;left:0;top:0;height:100%;width:{work_pct}%;'
        f'background:{color};border-radius:2px;"></div>'
        f'<div style="position:absolute;left:{time_pct}%;top:-2px;width:2px;height:8px;'
        f'background:{t["INK"]};border-radius:1px;opacity:0.3;"></div>'
        f'</div>'
    )

def _section_spacer() -> str:
    return '<tr><td style="padding-top:16px;"></td></tr>\n'

def _bullet_list(items: list[str], t: dict) -> str:
    return "".join(
        f'<p style="margin:0 0 6px;font-family:{t["FONT_UI"]};font-size:14px;'
        f'color:{t["TEXT"]};line-height:1.6;">'
        f'<span style="color:{t["GHOST"]};margin-right:8px;">—</span>{item}</p>'
        for item in items
    )

def _kv_row(label: str, value: str, t: dict) -> str:
    return (
        f'<tr>'
        f'<td style="padding:5px 16px 5px 0;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.08em;color:{t["GHOST"]};width:100px;vertical-align:top;">{label}</td>'
        f'<td style="padding:5px 0;font-family:{t["FONT_UI"]};font-size:14px;color:{t["TEXT"]};line-height:1.5;">{value}</td>'
        f'</tr>'
    )


def _project_activity_bullets(p: dict) -> tuple[list[str], list[str]]:
    """Use synthesized delivery/plan bullets first, then light fallbacks."""

    delivered = [str(item) for item in (p.get("delivered_bullets") or []) if str(item).strip()]
    planned = [str(item) for item in (p.get("planned_bullets") or []) if str(item).strip()]
    if delivered or planned:
        return delivered[:5], planned[:4]

    lin = p.get("linear_signals") or {}
    commits = p.get("commit_signals") or {}
    issues = p.get("issue_signals") or {}
    milestones = p.get("milestones") or []

    delivered_detail: list[str] = []
    planned_detail: list[str] = []

    quiet_repos = commits.get("quiet_repos") or []
    active_repos = commits.get("active_repos") or []
    if quiet_repos:
        delivered_detail.append(
            f"Silent repos: {', '.join(quiet_repos[:3])}"
            + (f" +{len(quiet_repos) - 3}" if len(quiet_repos) > 3 else "")
        )

    stale = issues.get("stale_count", 0) or lin.get("stale_count", 0)
    if stale > 0:
        top_stale = issues.get("top_stale", []) or lin.get("top_stale_issues", [])
        detail = f" — {top_stale[0]}" if top_stale else ""
        delivered_detail.append(f"{stale} stale issues not updated in 7+ days{detail}")

    bg = issues.get("backlog_growth", 0)
    if bg > 2:
        delivered_detail.append(f"Backlog grew by +{bg} issues")
    elif bg < -1:
        delivered_detail.append(f"Backlog shrank by {abs(bg)} issues")

    unowned = issues.get("unowned_count", 0)
    if unowned > 0:
        delivered_detail.append(f"{unowned} issues have no owner assigned")

    blocked_now = issues.get("blocked_threads", 0)
    if blocked_now > 0:
        top_blocked = issues.get("top_blocked", [])
        detail = f" — {top_blocked[0]}" if top_blocked else ""
        delivered_detail.append(f"{blocked_now} blocked threads{detail}")

    today_str = date.today().isoformat()
    upcoming = sorted(
        [m for m in milestones if m.get("target_date") and m["target_date"] >= today_str],
        key=lambda m: m["target_date"],
    )
    if upcoming:
        m = upcoming[0]
        planned_detail.append(f"Next milestone: {m['name']} — {m['target_date']}")
        if len(upcoming) > 1:
            planned_detail.append(f"Following: {upcoming[1]['name']} ({upcoming[1]['target_date']})")

    in_progress = lin.get("in_progress", 0)
    todo = lin.get("todo", 0)
    if in_progress > 0:
        planned_detail.append(f"{in_progress} issues currently in progress")
    if todo > 0:
        planned_detail.append(f"{todo} issues queued, ready to start")

    return delivered_detail[:5], planned_detail[:5]


# ── Section builders ──────────────────────────────────────────────────────────

def _html_header(report: SteeringReport, recipient: str, week_label: str, t: dict) -> str:
    total_projects = len(report.projects or [])
    active_projects = sum(1 for p in report.projects if p.status != "inactive")
    decisions = len(report.decisions_needed or [])
    attention = sum(1 for p in report.projects if p.status in {"at_risk", "off_track", "blocked"})
    inner = (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr>'
        f'<td style="width:44px;vertical-align:top;padding-right:14px;">'
        f'<div style="width:44px;height:44px;border:1px solid #111111;border-radius:8px;'
        f'font-family:{t["FONT_UI"]};font-size:22px;font-weight:800;color:{t["INK"]};'
        f'line-height:44px;text-align:center;">M</div>'
        f'</td>'
        f'<td style="vertical-align:top;">'
        f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:11px;font-weight:700;'
        f'letter-spacing:0.12em;text-transform:uppercase;color:{t["INK"]};">{t["COMPANY"]}</p>'
        f'<p style="margin:0 0 10px;font-family:{t["FONT_UI"]};font-size:12px;color:{t["GHOST"]};">'
        f'{report.generated_at[:10]}'
        f'</p>'
        f'<h1 style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:34px;font-weight:800;'
        f'color:{t["INK"]};letter-spacing:-0.04em;line-height:1.0;">Steering Report</h1>'
        f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:14px;color:{t["MUTED"]};line-height:1.5;">'
        f'{week_label} · For {recipient} · {active_projects}/{total_projects} active · {attention} need attention · {decisions} decisions'
        f'</p>'
        f'</td>'
        f'</tr>'
        f'</table>'
    )
    return (
        f'<tr><td style="padding-bottom:8px;border-bottom:2px solid #111111;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border-radius:0;padding:22px 0 20px;">'
        f'<tr><td>{inner}</td></tr></table></td></tr>\n'
    )


def _html_client_summary(text: str, t: dict) -> str:
    """Render the structured §Section client summary as labelled bullet lists."""
    # Parse §Section\nline\nline blocks
    sections: list[tuple[str, list[str]]] = []
    for block in text.strip().split("\n\n"):
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        if lines[0].startswith("§"):
            heading = lines[0][1:].strip()
            items = lines[1:]
        else:
            heading = ""
            items = lines
        if items:
            sections.append((heading, items))

    if not sections:
        # Fallback: plain paragraph for legacy string format
        inner = (
            _eyebrow("Weekly Summary", t)
            + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:14px;line-height:1.7;color:{t["INK"]};">{text}</p>'
        )
        return (
            f'<tr><td style="padding-top:12px;">'
            + _card(inner, t, padding="20px 24px")
            + f'</td></tr>\n'
        )

    section_colors = {
        "Delivered":      t["GREEN"],
        "Committed Next": t["MUTED"],
        "Risks":          t["RED"],
        "Inactive":       t["GHOST"],
    }

    html_sections = ""
    for i, (heading, items) in enumerate(sections):
        label_color = section_colors.get(heading, t["MUTED"])
        sep = f'<div style="height:1px;background:#f0f0f0;margin:14px 0;"></div>' if i > 0 else ""

        bullets_html = "".join(
            f'<p style="margin:0 0 5px;font-family:{t["FONT_UI"]};font-size:13px;'
            f'color:{t["TEXT"]};line-height:1.55;">'
            f'<span style="color:{t["GHOST"]};margin-right:7px;">—</span>{item}</p>'
            for item in items
        )
        html_sections += (
            sep
            + (f'<p style="margin:0 0 8px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
               f'color:{label_color};text-transform:uppercase;letter-spacing:0.10em;">{heading}</p>'
               if heading else "")
            + bullets_html
        )

    inner = _eyebrow("Weekly Summary", t) + html_sections
    return (
        f'<tr><td style="padding-top:12px;">'
        + _card(inner, t, padding="20px 24px")
        + f'</td></tr>\n'
    )


def _html_bottom_line(text: str, t: dict) -> str:
    inner = (
        _eyebrow("Bottom Line", t)
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:14px;line-height:1.6;color:{t["INK"]};font-weight:600;">{text}</p>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:#ffffff;border-left:4px solid #111111;border-radius:4px;">'
        f'<tr><td style="padding:20px 24px;">{inner}</td></tr>'
        f'</table>'
        + f'</td></tr>\n'
    )


def _html_stat_card(value: str, hint: str, accent: str | None, t: dict, is_cta: bool = False) -> str:
    """Single stat card — closer to the compact weekly-report metric tiles."""
    val_color = accent or t["INK"]
    has_signal = accent is not None or is_cta
    card_bg = "#111111" if has_signal else "#ffffff"
    text_color = "#ffffff" if has_signal else val_color
    hint_color = "#999999" if has_signal else t["MUTED"]
    card_border = "1px solid #222222" if has_signal else t["BORDER"]

    return (
        f'<td style="width:25%;padding:0 5px;vertical-align:top;height:112px;">'
        f'<div style="background:{card_bg};border:{card_border};border-radius:8px;padding:16px 14px;'
        f'height:112px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;">'
        f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:34px;font-weight:800;'
        f'color:{text_color};line-height:1.1;text-align:left;">{value}</p>'
        f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:11px;font-weight:600;'
        f'color:{hint_color};line-height:1.4;text-align:left;text-transform:uppercase;'
        f'letter-spacing:0.08em;">{hint}</p>'
        f'</div></td>'
    )


def _html_exec_snapshot(report: SteeringReport, projects: list[dict], t: dict) -> str:
    summary = report.portfolio_summary
    due_soon = sum(1 for p in projects if p.get("days_left") is not None and 0 <= p["days_left"] <= 14)
    high_eta = sum(1 for p in projects if p.get("eta_risk") in {"high", "critical"})
    inactive = summary.inactive if hasattr(summary, 'inactive') else 0
    active = max(summary.total_projects - inactive, 0)

    cards = (
        _html_stat_card(
            str(summary.on_track),
            f"On track · {active}/{summary.total_projects} active",
            None, t,
        )
        + _html_stat_card(
            str(summary.at_risk + getattr(summary, "off_track", 0)),
            "Need attention",
            t["ORANGE"] if (summary.at_risk + getattr(summary, "off_track", 0)) > 0 else None, t,
        )
        + _html_stat_card(
            str(due_soon),
            "Milestones in 14d",
            t["ORANGE"] if due_soon > 0 else None, t,
        )
        + _html_stat_card(
            str(summary.decisions_needed),
            "Decisions needed",
            t["RED"] if summary.decisions_needed > 0 else None, t,
            is_cta=summary.decisions_needed > 0,
        )
    )

    return (
        f'<tr><td style="padding-top:20px;">'
        + _eyebrow("Portfolio Health", t)
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-left:-5px;width:calc(100% + 10px);">'
        + f'<tr>{cards}</tr></table>'
        + f'</td></tr>\n'
    )


def _html_decisions(decisions: list[dict], t: dict) -> str:
    if not decisions:
        return ""

    rows_html = ""
    for i, d in enumerate(decisions):
        col = _status_color(d.get("status", "on_track"), t)
        border = f'border-bottom:1px solid #333333;' if i < len(decisions) - 1 else ""
        rows_html += (
            f'<div style="padding:14px 0;{border}">'
            f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px;">'
            f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
            f'background:{col};flex-shrink:0;margin-top:2px;"></span>'
            f'<span style="font-family:{t["FONT_UI"]};font-size:14px;font-weight:600;color:#ffffff;">{d.get("project","")}</span>'
            f'<span style="font-family:{t["FONT_UI"]};font-size:11px;color:#999999;">{d.get("owner","")}</span>'
            f'</div>'
            f'<p style="margin:0 0 0 14px;font-family:{t["FONT_UI"]};font-size:14px;color:#cccccc;line-height:1.5;">{d.get("text","")}</p>'
            f'</div>'
        )

    inner = (
        _eyebrow(f'Decisions Needed — {len(decisions)}', t, color=t["RED"])
        + rows_html
        + f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid #333333;">'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:11px;font-weight:600;'
        + f'color:#999999;text-transform:uppercase;letter-spacing:0.06em;">'
        + f'Action required this week ↑</p></div>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        + f'style="background:#111111;border:1px solid #222222;border-radius:8px;">'
        + f'<tr><td style="padding:24px;">{inner}</td></tr>'
        + f'</table>'
        + f'</td></tr>\n'
    )


def _html_week_summaries(this_week: list[str], next_week: list[str], t: dict) -> str:
    if not this_week and not next_week:
        return ""

    cols = ""
    if this_week:
        cols += (
            f'<td style="width:50%;vertical-align:top;padding-right:20px;">'
            + _eyebrow("Delivered This Week", t)
            + _bullet_list(this_week, t)
            + f'</td>'
        )
    if next_week:
        pad = f'border-left:{t["BORDER"]};padding-left:20px;' if this_week else ""
        cols += (
            f'<td style="width:50%;vertical-align:top;{pad}">'
            + _eyebrow("Next", t)
            + _bullet_list(next_week, t)
            + f'</td>'
        )

    inner = (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{cols}</tr></table>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + _card(inner, t)
        + f'</td></tr>\n'
    )


def _html_milestone_radar(projects: list[dict], week_start: str, t: dict) -> str:
    milestones = []
    for p in projects:
        for m in p.get("milestones") or []:
            if m.get("target_date") and m["target_date"] >= week_start:
                milestones.append((m["target_date"], p.get("name", ""), m.get("name", "")))
    milestones.sort(key=lambda x: x[0])
    if not milestones:
        return ""

    today = date.today().isoformat()
    rows_html = ""
    for i, (target_date, project_name, milestone_name) in enumerate(milestones[:8]):
        is_past = target_date < today
        border = f'border-bottom:1px solid #f0f0f0;' if i < min(len(milestones), 8) - 1 else ""
        date_color = t["GHOST"] if is_past else t["INK"]
        rows_html += (
            f'<tr style="{border}">'
            f'<td style="padding:8px 16px 8px 0;font-family:{t["FONT_MONO"]};font-size:11px;'
            f'color:{date_color};white-space:nowrap;width:90px;">{target_date}</td>'
            f'<td style="padding:8px 16px 8px 0;font-family:{t["FONT_UI"]};font-size:12px;'
            f'font-weight:600;color:{t["INK"]};width:140px;">{project_name}</td>'
            f'<td style="padding:8px 0;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};">{milestone_name}</td>'
            f'</tr>'
        )

    inner = (
        _eyebrow("Milestone Radar", t)
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0">{rows_html}</table>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + _card_warm(inner, t)
        + f'</td></tr>\n'
    )


def _html_portfolio_table(projects: list, t: dict) -> str:
    header = (
        f'<tr style="border-bottom:{t["BORDER_MED"]};">'
        + "".join(
            f'<td style="padding:8px 12px 10px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:600;'
            f'text-transform:uppercase;letter-spacing:0.08em;color:{t["GHOST"]};">{col}</td>'
            for col in ["Project", "Delivery", "Score", "Status", "Decision", "Next Milestone"]
        )
        + "</tr>\n"
    )
    rows = ""
    for i, p in enumerate(projects):
        work = int(p.get("work_progress_pct", 0))
        time_p = int(p.get("time_progress_pct", 0))
        col = _status_color(p.get("status", "on_track"), t)
        border = f'border-bottom:1px solid #f0f0f0;' if i < len(projects) - 1 else ""

        bar_w = 110
        filled_w = min(int(work * bar_w / 100), bar_w)
        cursor_w = min(int(time_p * bar_w / 100), bar_w - 2)
        bar = (
            f'<div style="width:{bar_w}px;">'
            f'<div style="position:relative;height:4px;background:#e5e5e5;border-radius:2px;">'
            f'<div style="position:absolute;left:0;top:0;height:100%;width:{filled_w}px;background:{col};border-radius:2px;"></div>'
            f'<div style="position:absolute;left:{cursor_w}px;top:-1px;width:2px;height:6px;background:#000;border-radius:1px;opacity:0.2;"></div>'
            f'</div>'
            f'<p style="margin:3px 0 0;font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};">{work}%</p>'
            f'</div>'
        )
        status_pill = _pill(
            _status_label(p.get("status", "on_track")),
            "#ffffff",
            _status_bg(p.get("status", "on_track")),
            _status_border(p.get("status", "on_track")),
        )

        score = int(p.get("health_score", 0))
        trend = p.get("score_trend") or {}
        trend_display = trend.get("display", "")
        trend_color = {
            "up": t["GREEN"], "down": t["RED"], "flat": t["GHOST"], "new": t["MUTED"]
        }.get(trend.get("movement", "new"), t["GHOST"])

        target = p.get("target_date") or "—"
        days = p.get("days_left")
        days_color = t["RED"] if (days or 99) < 14 else t["GHOST"]
        days_html = f'<br><span style="font-size:10px;color:{days_color};">{days}d</span>' if days is not None else ""
        decision = p.get("decision_needed") or "—"

        rows += (
            f'<tr style="{border}">'
            f'<td style="padding:10px 12px;font-family:{t["FONT_UI"]};font-size:13px;font-weight:700;color:{t["INK"]};">'
            f'{p.get("name","")}'
            f'<div style="margin-top:4px;font-size:11px;font-weight:500;color:{t["GHOST"]};">{p.get("owner","")}</div>'
            f'</td>'
            f'<td style="padding:10px 12px;">{bar}</td>'
            f'<td style="padding:10px 12px;font-family:{t["FONT_MONO"]};font-size:12px;font-weight:700;color:{_score_text_color(score)};">{score}'
            f'<div style="margin-top:4px;font-family:{t["FONT_UI"]};font-size:11px;font-weight:600;color:{trend_color};">{trend_display or "—"}</div>'
            f'</td>'
            f'<td style="padding:10px 12px;">'
            f'{status_pill}'
            f'</td>'
            f'<td style="padding:10px 12px;font-family:{t["FONT_UI"]};font-size:12px;color:{t["MUTED"]};max-width:180px;">{decision}</td>'
            f'<td style="padding:10px 12px;font-family:{t["FONT_MONO"]};font-size:11px;color:{t["MUTED"]};white-space:nowrap;">{target}{days_html}</td>'
            f'</tr>\n'
        )

    inner = (
        _eyebrow(f'Portfolio — {len(projects)} Projects', t)
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0">{header}{rows}</table>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + _card(inner, t, padding="20px 24px")
        + f'</td></tr>\n'
    )


def _project_needs_detail(p: dict) -> bool:
    trend = p.get("score_trend") or {}
    delta = abs(int(trend.get("delta", 0) or 0))
    return (
        p.get("status") != "on_track"
        or bool(p.get("decision_needed"))
        or delta >= 8
    )


def _html_project_card_compact(p: dict, t: dict) -> str:
    """Compact read-only card for On Track projects — delivered + next week only."""
    done_bullets, next_bullets = _project_activity_bullets(p)

    name_html = (
        f'<span style="font-family:{t["FONT_UI"]};font-size:14px;font-weight:700;color:{t["INK"]};">'
        f'{p.get("name","")}</span>'
        f'<span style="font-family:{t["FONT_UI"]};font-size:11px;color:{t["MUTED"]};margin-left:8px;">'
        f'{p.get("owner","")}</span>'
    )

    score_val = int(p.get("health_score", 0))
    trend = p.get("score_trend") or {}
    trend_disp = trend.get("display", "")
    trend_mv = trend.get("movement", "new")
    trend_color = {"up": t["GREEN"], "down": t["RED"], "flat": t["GHOST"], "new": t["MUTED"]}.get(trend_mv, t["GHOST"])
    score_html = (
        f'<span style="font-family:{t["FONT_MONO"]};font-size:11px;font-weight:700;color:{t["GREEN"]};">{score_val}</span>'
        f'<span style="font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};margin-left:1px;">/100</span>'
    )
    if trend_disp and trend_mv != "new":
        score_html += (
            f'<span style="font-family:{t["FONT_MONO"]};font-size:10px;font-weight:600;'
            f'color:{trend_color};margin-left:5px;">{trend_disp}</span>'
        )

    work = int(p.get("work_progress_pct", 0))
    time_pct = int(p.get("time_progress_pct", 0))
    target = p.get("target_date") or ""
    days_left = p.get("days_left")
    target_str = target if target else ""
    if days_left is not None:
        target_str += f" · {days_left}d"

    header_html = (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td style="vertical-align:middle;">{name_html}</td>'
        f'<td align="right" style="vertical-align:middle;white-space:nowrap;">'
        + _pill("On Track", "#ffffff", "#16a34a", "1px solid #16a34a")
        + f'<span style="margin-left:8px;">{score_html}</span>'
        + f'</td></tr></table>'
    )

    progress_html = (
        f'<div style="margin-top:10px;">'
        + _progress_bar(work, time_pct, t["GREEN"], t)
        + f'<p style="margin:4px 0 0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["MUTED"]};">'
        f'<strong style="color:{t["INK"]};">{work}%</strong> done'
        f' &nbsp;/&nbsp; {time_pct}% elapsed'
        + (f' &nbsp;·&nbsp; <span style="color:{t["GHOST"]};">{target_str}</span>' if target_str else "")
        + f'</p></div>'
    )

    cols = ""
    if done_bullets:
        items_html = "".join(
            f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};line-height:1.5;">'
            f'<span style="color:{t["GHOST"]};margin-right:6px;">—</span>{b}</p>'
            for b in done_bullets[:4]
        )
        cols += (
            f'<td style="width:50%;vertical-align:top;padding-right:16px;">'
            + _eyebrow("Delivered", t)
            + items_html
            + f'</td>'
        )

    if next_bullets:
        items_html = "".join(
            f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};line-height:1.5;">'
            f'<span style="color:{t["GHOST"]};margin-right:6px;">—</span>{b}</p>'
            for b in next_bullets[:3]
        )
        pad = f'border-left:{t["BORDER"]};padding-left:16px;' if done_bullets else ""
        cols += (
            f'<td style="width:50%;vertical-align:top;{pad}">'
            + _eyebrow("Next Week", t)
            + items_html
            + f'</td>'
        )

    body_html = ""
    if cols:
        body_html = (
            f'<div style="margin-top:12px;border-top:1px solid #f0f0f0;padding-top:12px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{cols}</tr></table>'
            f'</div>'
        )

    inner = header_html + progress_html + body_html
    return (
        f'<tr><td style="padding-bottom:8px;">'
        + _card(inner, t, padding="16px 20px")
        + f'</td></tr>\n'
    )


def _html_project_card(p: dict, sp_trend: str, t: dict) -> str:
    col = _status_color(p.get("status", "on_track"), t)
    work = int(p.get("work_progress_pct", 0))
    time_pct = int(p.get("time_progress_pct", 0))
    eta = p.get("eta_risk", "low")
    status = p.get("status", "on_track")

    target = p.get("target_date", "")
    days_left = p.get("days_left")
    target_str = target if target else "No target date"
    if target and days_left is not None:
        target_str += f" · {days_left}d left"

    today_str = date.today().isoformat()
    milestones = p.get("milestones") or []
    sorted_ms = sorted(milestones, key=lambda m: m.get("target_date", ""))
    upcoming_ms = [m for m in sorted_ms if m.get("target_date", "") >= today_str]
    past_ms = [m for m in sorted_ms if m.get("target_date", "") < today_str]
    next_milestone = upcoming_ms[0] if upcoming_ms else None
    ms_position = f"{len(past_ms)}/{len(sorted_ms)} milestones passed" if sorted_ms else None
    done_bullets, next_bullets = _project_activity_bullets(p)
    health_signals = p.get("health_signals", [])
    blockers = p.get("blockers", [])

    vel_note = ""
    if sp_trend == "declining":
        vel_note = f'&nbsp; <span style="color:{t["RED"]};font-size:10px;font-weight:500;">↓ team velocity</span>'
    elif sp_trend == "improving":
        vel_note = f'&nbsp; <span style="color:{t["GREEN"]};font-size:10px;font-weight:500;">↑ team velocity</span>'

    attention = "Immediate" if status == "off_track" else "Leadership" if blockers else "Monitor" if health_signals else "None"

    # ── Card header with status pill ──────────────────────────────────────────
    card_border = t["BORDER"] if status == "on_track" else f"1px solid {col}33"
    status_pill = _pill(_status_label(status), _status_text_color(status), _status_bg(status), _status_border(status))

    # Trend indicator
    score_val = int(p.get("health_score", 0))
    trend = p.get("score_trend") or {}
    trend_disp = trend.get("display", "")
    trend_mv = trend.get("movement", "new")
    trend_color = {
        "up": t["GREEN"], "down": t["RED"], "flat": t["GHOST"], "new": t["MUTED"]
    }.get(trend_mv, t["GHOST"])
    if trend_disp and trend_mv != "new":
        score_display = (
            f'<span style="font-family:{t["FONT_MONO"]};font-size:12px;font-weight:700;'
            f'color:{_score_text_color(score_val)};">{score_val}</span>'
            f'<span style="font-family:{t["FONT_MONO"]};font-size:10px;font-weight:600;'
            f'color:{trend_color};margin-left:6px;">{trend_disp}</span>'
            f'<span style="font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};margin-left:2px;">/100</span>'
        )
    else:
        score_display = (
            f'<span style="font-family:{t["FONT_MONO"]};font-size:12px;font-weight:700;'
            f'color:{_score_text_color(score_val)};">{score_val}</span>'
            f'<span style="font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};margin-left:2px;">/100</span>'
        )

    header_html = (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr>'
        f'<td style="vertical-align:middle;">'
        f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{t["GHOST"]};">'
        f'Project Card</p>'
        f'<span style="font-family:{t["FONT_UI"]};font-size:16px;font-weight:700;color:{t["INK"]};letter-spacing:-0.01em;">{p.get("name","")}</span>'
        f'<span style="font-family:{t["FONT_UI"]};font-size:12px;color:{t["MUTED"]};margin-left:10px;">{p.get("owner","")}</span>'
        f'</td>'
        f'<td align="right" style="vertical-align:middle;white-space:nowrap;">'
        + status_pill
        + f'<span style="margin-left:10px;">{score_display}</span>'
        + f'</td></tr></table>'
    )

    # ── Timeline strip ────────────────────────────────────────────────────────
    timeline_html = (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:12px;">'
        f'<tr>'
        f'<td style="vertical-align:top;">'
        + _progress_bar(work, time_pct, col, t)
        + f'<p style="margin:5px 0 0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["MUTED"]};">'
        f'<strong style="color:{t["INK"]};">{work}%</strong> done'
        f' &nbsp;/&nbsp; {time_pct}% elapsed'
        f' &nbsp;·&nbsp; ETA: <span style="color:{_eta_color(eta, t)};font-weight:600;">{_eta_label(eta)}</span>'
        + vel_note
        + f'<br><span style="font-size:10px;color:{t["GHOST"]};">{_forecast_label(p.get("forecast","delivering_as_planned"))}</span>'
        f'</p></td>'
        f'<td style="width:160px;text-align:right;vertical-align:top;padding-left:16px;">'
        f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:12px;color:{t["INK"]};font-weight:600;">{target_str.split("·")[0].strip()}</p>'
        + (f'<p style="margin:2px 0 0;font-family:{t["FONT_UI"]};font-size:10px;color:{t["MUTED"]};">{target_str.split("·")[1].strip()}</p>' if "·" in target_str else "")
        + (f'<p style="margin:4px 0 0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["INK"]};font-weight:600;">▸ {next_milestone["name"]}</p><p style="margin:1px 0 0;font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};">{next_milestone["target_date"]}</p>' if next_milestone else "")
        + (f'<p style="margin:2px 0 0;font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};">{ms_position}</p>' if ms_position else "")
        + f'</td></tr></table>'
    )

    # ── Plan snapshot + milestones row ────────────────────────────────────────
    lin = p.get("linear_signals", {})
    plan_rows = [
        ("State",   _project_state_label(p.get("linear_state"))),
        ("Start",   p.get("start_date") or "Not set"),
        ("Target",  _date_label(p.get("target_date"))),
        ("Issues",  f'{lin.get("total_issues",0)} total · {lin.get("completed",0)} done · {lin.get("in_progress",0)} in progress · {lin.get("todo",0)} todo'),
    ]
    plan_html = (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        + "".join(_kv_row(label, value, t) for label, value in plan_rows)
        + f'</table>'
    )

    if sorted_ms:
        ms_items = ""
        for m in sorted_ms[:5]:
            is_past = m.get("target_date", "") < today_str
            ms_items += (
                f'<p style="margin:0 0 6px;font-family:{t["FONT_UI"]};font-size:12px;color:{t["MUTED"] if is_past else t["TEXT"]};">'
                f'<span style="color:{t["GHOST"] if is_past else t["INK"]};margin-right:6px;">{"✓" if is_past else "—"}</span>'
                f'{m.get("name","")}'
                f'<span style="color:{t["GHOST"]};font-size:10px;margin-left:6px;">{m.get("target_date","")}</span>'
                f'</p>'
            )
        ms_col = (
            _eyebrow("Milestones", t)
            + ms_items
        )
    else:
        ms_col = _eyebrow("Milestones", t) + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:12px;color:{t["GHOST"]};">None in Linear</p>'

    plan_sep = f'<div style="height:1px;background:#f0f0f0;margin-top:14px;"></div>'
    plan_section = (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;">'
        f'<tr>'
        f'<td style="width:48%;vertical-align:top;padding-right:16px;">'
        + _eyebrow("Plan Snapshot", t) + plan_html
        + f'</td>'
        f'<td style="width:52%;vertical-align:top;border-left:{t["BORDER"]};padding-left:16px;">'
        + ms_col
        + f'</td></tr></table>'
    )

    # ── Signal rows ───────────────────────────────────────────────────────────
    signal_rows = ""
    status_row = (
        f'<div style="border-top:1px solid #d4d4d4;padding-top:12px;margin-top:12px;">'
        + _eyebrow("Status", t)
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:2px;">'
        + f'<tr>'
        + f'<td style="width:33.33%;vertical-align:top;padding-right:10px;">'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["GHOST"]};text-transform:uppercase;letter-spacing:0.06em;">Trend</p>'
        + f'<p style="margin:5px 0 0;font-family:{t["FONT_UI"]};font-size:14px;font-weight:700;color:{trend_color};">{trend_disp or "—"}</p>'
        + f'</td>'
        + f'<td style="width:33.33%;vertical-align:top;padding-right:10px;">'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["GHOST"]};text-transform:uppercase;letter-spacing:0.06em;">Attention</p>'
        + f'<p style="margin:5px 0 0;font-family:{t["FONT_UI"]};font-size:14px;font-weight:700;color:{t["INK"]};">{attention}</p>'
        + f'</td>'
        + f'<td style="width:33.33%;vertical-align:top;">'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["GHOST"]};text-transform:uppercase;letter-spacing:0.06em;">Decision</p>'
        + f'<p style="margin:5px 0 0;font-family:{t["FONT_UI"]};font-size:14px;font-weight:700;color:{t["INK"]};">{p.get("decision_needed") or "No"}</p>'
        + f'</td>'
        + f'</tr></table>'
        + f'</div>'
    )
    signal_rows += status_row

    # This Week: one-liner headline + risk/warning details only
    delta = p.get("week_delta")
    if delta or done_bullets:
        signal_rows += (
            f'<div style="border-top:1px solid #d4d4d4;padding-top:12px;margin-top:12px;">'
            + _eyebrow("This Week", t)
        )
        if delta:
            signal_rows += (
                f'<p style="margin:0 0 8px;font-family:{t["FONT_UI"]};font-size:14px;'
                f'color:{t["INK"]};font-weight:600;line-height:1.6;">{delta}</p>'
            )
        # Detail bullets — only risk signals, never repeat counts the one-liner covers
        if done_bullets:
            for item in done_bullets:
                signal_rows += (
                    f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:13px;'
                    f'color:{t["MUTED"]};line-height:1.5;">— {item}</p>'
                )
        signal_rows += f'</div>'
    elif not delta and not done_bullets:
        # Nothing to show — skip section entirely
        pass

    if health_signals:
        signal_rows += (
            f'<div style="border-top:1px solid #d4d4d4;padding-top:12px;margin-top:12px;">'
            + _eyebrow("Risks & Signals", t, color=t["RED"])
            + "".join(f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};line-height:1.5;">— {b}</p>' for b in health_signals[:3])
            + f'</div>'
        )

    if blockers:
        signal_rows += (
            f'<div style="border-top:1px solid #d4d4d4;padding-top:12px;margin-top:12px;">'
            + _eyebrow("Blockers", t, color=t["RED"])
            + "".join(f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};line-height:1.5;">— {b}</p>' for b in blockers[:2])
            + f'</div>'
        )

    # Meeting signal from Granola
    meeting = p.get("meeting_signal")
    if meeting:
        signal_rows += (
            f'<div style="border-top:1px solid #d4d4d4;padding-top:12px;margin-top:12px;'
            f'background:{t["CARD_WARM"]};border-radius:6px;padding:12px;">'
            + _eyebrow("From Meetings", t)
            + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};font-style:italic;line-height:1.5;">{meeting}</p>'
            + f'</div>'
        )

    # Next Week: one-liner headline + complementary details
    next_week_text = p.get("next_week")
    if next_week_text or next_bullets:
        signal_rows += (
            f'<div style="border-top:1px solid #d4d4d4;padding-top:12px;margin-top:12px;">'
            + _eyebrow("Next Week", t)
        )
        if next_week_text:
            signal_rows += (
                f'<p style="margin:0 0 10px;font-family:{t["FONT_UI"]};font-size:14px;'
                f'color:{t["INK"]};font-weight:600;line-height:1.6;">{next_week_text}</p>'
            )
        # Show only bullets that add detail beyond the one-liner
        extra_next = [
            b for b in next_bullets
            if not next_week_text or b.lower() not in next_week_text.lower()
        ]
        for item in extra_next[:4]:
            signal_rows += (
                f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:13px;'
                f'color:{t["MUTED"]};line-height:1.5;">— {item}</p>'
            )
        if not next_week_text and not extra_next:
            for item in next_bullets[:4]:
                signal_rows += (
                    f'<p style="margin:0 0 4px;font-family:{t["FONT_UI"]};font-size:13px;'
                    f'color:{t["TEXT"]};line-height:1.5;">— {item}</p>'
                )
        signal_rows += f'</div>'

    card_inner = header_html + timeline_html + plan_section + signal_rows
    return (
        f'<tr><td style="padding-bottom:12px;">'
        + _card(card_inner, t, padding="20px 24px", border=card_border)
        + f'</td></tr>\n'
    )


def _html_cross_project(risks: list[str], t: dict) -> str:
    if not risks:
        return ""
    inner = (
        _eyebrow("Cross-Project Signals", t)
        + "".join(
            f'<p style="margin:0 0 5px;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};line-height:1.5;">— {r}</p>'
            for r in risks
        )
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + _card_warm(inner, t)
        + f'</td></tr>\n'
    )


def _html_sprint_pulse(sp: dict, t: dict) -> str:
    if not sp or not sp.get("sprint_name"):
        return ""
    days_left = sp.get("days_remaining_in_sprint")
    days_str = f" · {days_left}d left" if days_left is not None else ""
    trend = sp.get("velocity_trend", "stable")
    trend_html = {
        "declining": f'<span style="color:{t["RED"]};font-weight:600;">↓ Declining</span>',
        "improving": f'<span style="color:{t["GREEN"]};font-weight:600;">↑ Improving</span>',
        "stable":    f'<span style="color:{t["MUTED"]};">→ Stable</span>',
    }.get(trend, f'<span style="color:{t["MUTED"]};">—</span>')
    sprint_status = sp.get("sprint_status", "unknown")
    status_dot = {
        "on_track":  f'<span style="color:{t["GREEN"]};">●</span> On track',
        "at_risk":   f'<span style="color:{t["ORANGE"]};">●</span> At risk',
        "off_track": f'<span style="color:{t["RED"]};">●</span> Off track',
    }.get(sprint_status, "")

    inner = (
        _eyebrow(f'Sprint Pulse · {sp["sprint_name"]}{days_str}', t)
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        + f'<td style="width:50%;vertical-align:top;">'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};">'
        + f'<strong style="color:{t["INK"]};font-size:20px;">{int(sp.get("sprint_completion_rate", 0))}%</strong> done'
        + f' &nbsp;/&nbsp; {int(sp.get("sprint_time_progress", 0))}% elapsed &nbsp; {status_dot}</p>'
        + f'</td>'
        + f'<td style="width:50%;vertical-align:top;border-left:{t["BORDER"]};padding-left:20px;">'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};">'
        + f'<strong style="color:{t["INK"]};font-size:20px;">{sp.get("velocity_avg", 0)}</strong> pts/day'
        + f' &nbsp; {trend_html}'
        + f'<br><span style="font-size:10px;color:{t["GHOST"]};">avg last {sp.get("cycles_analyzed", 0)} sprints</span>'
        + f'</p></td></tr></table>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + _card(inner, t)
        + f'</td></tr>\n'
    )


def _html_capacity(ooo: list[str], t: dict) -> str:
    if not ooo:
        return ""
    inner = (
        _eyebrow("Team Capacity", t)
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:13px;color:{t["TEXT"]};">'
        + f'Out of office: <strong style="color:{t["INK"]};">{", ".join(ooo)}</strong>'
        + f'</p>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + _card_warm(inner, t)
        + f'</td></tr>\n'
    )


def _html_inactive_group(ig: dict | None, t: dict) -> str:
    """Collapsed view of stalled/incubation projects — one compact card."""
    if not ig or ig.get("count", 0) == 0:
        return ""
    count = ig.get("count", 0)
    projects = ig.get("projects", [])
    summary = ig.get("summary", "")

    inner = (
        _eyebrow(f'Inactive Projects — {count}', t, color=t["MUTED"])
        + f'<p style="margin:0 0 6px;font-family:{t["FONT_UI"]};font-size:13px;'
        + f'color:{t["TEXT"]};line-height:1.6;">{summary}</p>'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:11px;color:{t["GHOST"]};">'
        + f'{", ".join(projects[:6])}'
        + (f' +{len(projects) - 6} more' if len(projects) > 6 else '')
        + f'</p>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + _card_warm(inner, t, padding="16px 24px")
        + f'</td></tr>\n'
    )


def _html_portfolio_risks(risks: list[str], t: dict) -> str:
    if not risks:
        return ""
    inner = (
        _eyebrow("Portfolio Risks", t)
        + "".join(
            f'<p style="margin:0 0 6px;font-family:{t["FONT_UI"]};font-size:13px;'
            f'color:{t["TEXT"]};line-height:1.6;">'
            f'<span style="color:{t["RED"]};margin-right:8px;">▸</span>{r}</p>'
            for r in risks
        )
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        + f'style="background:#ffffff;border:1px solid #fca5a5;border-radius:8px;'
        + f'box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
        + f'<tr><td style="padding:20px 24px;">{inner}</td></tr>'
        + f'</table>'
        + f'</td></tr>\n'
    )


def _html_leadership_priorities(priorities: list[str], t: dict) -> str:
    if not priorities:
        return ""
    items = ""
    for i, p in enumerate(priorities):
        items += (
            f'<div style="padding:12px 0;'
            + (f'border-bottom:1px solid #333333;' if i < len(priorities) - 1 else '')
            + f'">'
            f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:14px;'
            f'color:#ffffff;font-weight:600;line-height:1.6;">{p}</p>'
            f'</div>'
        )
    inner = (
        _eyebrow("Leadership Priorities — This Week", t, color=t["RED"])
        + items
        + f'<p style="margin:12px 0 0;font-family:{t["FONT_UI"]};font-size:10px;'
        + f'color:#999999;text-transform:uppercase;letter-spacing:0.06em;">'
        + f'Ranked by urgency and impact ↑</p>'
    )
    return (
        f'<tr><td style="padding-top:16px;">'
        + f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        + f'style="background:#111111;border:1px solid #222222;border-radius:8px;'
        + f'box-shadow:0 2px 6px rgba(0,0,0,0.12);">'
        + f'<tr><td style="padding:24px;">{inner}</td></tr>'
        + f'</table>'
        + f'</td></tr>\n'
    )


def _html_score_methodology(text: str, t: dict) -> str:
    if not text:
        return ""
    return (
        f'<tr><td style="padding-top:28px;">'
        + f'<p style="margin:0;font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};'
        + f'line-height:1.6;text-align:center;">{text}</p>'
        + f'</td></tr>\n'
    )


def _html_footer(sources: list[str], errors: list[str], t: dict) -> str:
    errors_html = (
        f' &nbsp;·&nbsp; <span style="color:{t["ORANGE"]};">partial data</span>'
        if errors else ""
    )
    return (
        f'<tr><td style="padding-top:40px;border-top:{t["BORDER"]};">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td><p style="margin:0;font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};">'
        f'<strong style="color:{t["MUTED"]};">{t["COMPANY"]}</strong>'
        f' &nbsp;·&nbsp; {t["LOCATION"]}'
        f' &nbsp;·&nbsp; {t["TAGLINE"]}</p></td>'
        f'<td align="right"><p style="margin:0;font-family:{t["FONT_UI"]};font-size:10px;color:{t["GHOST"]};">'
        f'Signals: {", ".join(sources) or "none"}{errors_html}</p></td>'
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
        recipient = raw.split("<")[0].strip() if "<" in raw else ("Recipient" if "@" in raw else raw or "Recipient")
    except Exception:
        recipient = "Recipient"

    from tools.steering_schema import report_to_dict
    d = report_to_dict(report)
    projects = d.get("projects", [])
    sp = d.get("sprint_signals") or {}
    sp_trend = sp.get("velocity_trend", "stable")

    rows = ""
    rows += _html_header(report, recipient, week_label, t)

    rows += _html_bottom_line(report.portfolio_summary.top_risk or "No summary.", t)
    rows += _html_exec_snapshot(report, projects, t)

    # Inactive projects (collapsed — reduce noise)
    ig = d.get("inactive_group")
    if ig:
        rows += _html_inactive_group(ig, t)

    rows += _html_portfolio_table(projects, t)
    rows += _html_week_summaries(d.get("this_week_summary", []), d.get("next_week_summary", []), t)
    if report.client_summary:
        rows += _html_client_summary(report.client_summary, t)
    rows += _html_decisions(d.get("decisions_needed", []), t)
    rows += _html_sprint_pulse(sp, t)
    rows += _html_milestone_radar(projects, report.week_start, t)

    detail_projects = [p for p in projects if _project_needs_detail(p)]
    on_track_projects = [p for p in projects if not _project_needs_detail(p)]

    if detail_projects:
        rows += (
            f'<tr><td style="padding-top:24px;">'
            + _eyebrow("Project Detail", t)
            + f'</td></tr>\n'
        )
        for p in detail_projects:
            rows += _html_project_card(p, sp_trend, t)

    if on_track_projects:
        rows += (
            f'<tr><td style="padding-top:20px;">'
            + _eyebrow("On Track", t, color=t["GREEN"])
            + f'</td></tr>\n'
        )
        for p in on_track_projects:
            rows += _html_project_card_compact(p, t)

    # Portfolio risks (cross-cutting patterns)
    rows += _html_portfolio_risks(d.get("portfolio_summary", {}).get("portfolio_risks", []), t)

    # Leadership priorities
    rows += _html_leadership_priorities(d.get("portfolio_summary", {}).get("leadership_priorities", []), t)

    rows += _html_cross_project(d.get("cross_project_risks", []), t)

    ooo = (d.get("capacity_signals") or {}).get("ooo_this_week", [])
    rows += _html_capacity(ooo, t)

    # Score methodology (small text at bottom)
    methodology = report.score_methodology
    if methodology:
        rows += _html_score_methodology(methodology, t)

    rows += _html_footer(report.sources, report.errors, t)

    return (
        f'<!DOCTYPE html><html lang="en"><head>'
        f'<meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f'<title>Steering Report — {week_label}</title>'
        f'</head>'
        f'<body style="margin:0;padding:0;background:{t["BG"]};'
        f'font-family:{t["FONT_UI"]};color:{t["TEXT"]};-webkit-font-smoothing:antialiased;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:{t["BG"]};padding:40px 0 72px;">'
        f'<tr><td align="center">'
        f'<table width="680" cellpadding="0" cellspacing="0" border="0" style="max-width:680px;width:100%;padding:0 24px;">'
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

    lines.append(f"## Portfolio ({s.total_projects} projects)")
    lines.append("")
    lines.append("| Project | Progress | Trend | Status | Decision | Target | Days |")
    lines.append("|---------|----------|-------|--------|----------|--------|------|")
    N = 20
    for p in report.projects:
        work_p = int(p.work_progress_pct)
        time_p = int(p.time_progress_pct)
        filled = round(work_p * N / 100)
        cursor = min(round(time_p * N / 100), N - 1)
        bar = list("█" * filled + "░" * (N - filled))
        bar[cursor] = "↑"
        trend = p.score_trend.display if p.score_trend and p.score_trend.display else "—"
        decision = p.decision_needed or "—"
        lines.append(
            f"| {p.name} | `{''.join(bar)}` {work_p}% "
            f"| {trend} "
            f"| {p.status.replace('_',' ').title()} "
            f"| {decision} "
            f"| {p.target_date or '—'} | {p.days_left if p.days_left is not None else '—'} |"
        )
    lines.append("")

    if report.this_week_summary:
        lines.append("## This Week")
        lines.append("")
        for b in report.this_week_summary:
            lines.append(f"- {b}")
        lines.append("")

    if report.next_week_summary:
        lines.append("## Next Week")
        lines.append("")
        for b in report.next_week_summary:
            lines.append(f"- {b}")
        lines.append("")

    if report.client_summary:
        lines.append("## Weekly Summary")
        lines.append("")
        for block in report.client_summary.strip().split("\n\n"):
            block_lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
            if not block_lines:
                continue
            if block_lines[0].startswith("§"):
                lines.append(f"**{block_lines[0][1:].strip()}**")
                for item in block_lines[1:]:
                    lines.append(f"- {item}")
            else:
                for item in block_lines:
                    lines.append(f"- {item}")
            lines.append("")

    if report.decisions_needed:
        lines.append(f"## Decisions Needed ({len(report.decisions_needed)})")
        lines.append("")
        for d in report.decisions_needed:
            lines.append(f"- **{d['project']}** ({d['owner']}): {d['text']}")
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
            f"Velocity: **{sp.velocity_avg} pts/day** (last {sp.cycles_analyzed} sprints) "
            f"{trend_icon} {sp.velocity_trend.replace('_', ' ').title()}"
        )
        lines.append("")

    milestone_rows = []
    for p in report.projects:
        for m in p.milestones:
            if m.get("target_date") and m["target_date"] >= report.week_start:
                milestone_rows.append((m["target_date"], p.name, m.get("name", "")))
    milestone_rows.sort(key=lambda x: x[0])
    if milestone_rows:
        lines.append("## Milestone Radar")
        lines.append("")
        for target_date, project_name, milestone_name in milestone_rows[:8]:
            lines.append(f"- {target_date} — **{project_name}**: {milestone_name}")
        lines.append("")

    def _needs_detail_card(p) -> bool:
        return _project_needs_detail({
            "status": p.status,
            "decision_needed": p.decision_needed,
            "score_trend": {"delta": p.score_trend.delta if p.score_trend else 0},
        })

    detail_projects = [p for p in report.projects if _needs_detail_card(p)]
    on_track_projects = [p for p in report.projects if not _needs_detail_card(p)]

    if detail_projects:
        lines.append("## Project Detail")
        lines.append("")
    for p in detail_projects:
        done_bullets, next_bullets = _project_activity_bullets({
            "linear_signals": {
                "completed": p.linear_signals.completed,
                "in_progress": p.linear_signals.in_progress,
                "todo": p.linear_signals.todo,
            },
            "commit_signals": {
                "commits_this_week": p.commit_signals.commits_this_week,
                "active_repos": p.commit_signals.active_repos,
                "quiet_repos": p.commit_signals.quiet_repos,
            },
            "issue_signals": {
                "stale_count": p.issue_signals.stale_count,
                "top_stale": p.issue_signals.top_stale,
                "backlog_growth": p.issue_signals.backlog_growth,
                "unowned_count": p.issue_signals.unowned_count,
                "blocked_threads": p.issue_signals.blocked_threads,
                "top_blocked": p.issue_signals.top_blocked,
            },
            "milestones": p.milestones,
            "delivered_bullets": p.delivered_bullets,
            "planned_bullets": p.planned_bullets,
            "next_week": p.next_week,
        })
        lines.append(f"### {p.name} — {p.owner}")
        lines.append("")
        lines.append(
            f"**Timeline:** {int(p.work_progress_pct)}% done / {int(p.time_progress_pct)}% elapsed"
            + (f" · **{p.days_left}d left**" if p.days_left is not None else "")
            + (f" · target {p.target_date}" if p.target_date else "")
        )
        lines.append(f"**ETA:** {p.eta_risk.upper()} · **Score:** {int(p.health_score)}/100")
        lines.append(
            f"**Linear:** state {_project_state_label(p.linear_state)}"
            f" · start {p.start_date or 'Not set'}"
            f" · target {p.target_date or 'No target date'}"
        )
        lines.append(
            f"**Issues:** {p.linear_signals.total_issues} total"
            f" · {p.linear_signals.completed} done"
            f" · {p.linear_signals.in_progress} in progress"
            f" · {p.linear_signals.todo} todo"
        )
        if p.milestones:
            today_str = date.today().isoformat()
            sorted_ms = sorted(p.milestones, key=lambda m: m.get("target_date", ""))
            past = [m for m in sorted_ms if m.get("target_date", "") < today_str]
            upcoming = [m for m in sorted_ms if m.get("target_date", "") >= today_str]
            if upcoming:
                lines.append(f"**Next milestone:** {upcoming[0]['name']} — {upcoming[0]['target_date']}")
            lines.append(f"**Milestones:** {len(past)}/{len(sorted_ms)} passed")
            for m in sorted_ms[:6]:
                status = "✓" if m.get("target_date", "") < today_str else "·"
                lines.append(f"  {status} {m.get('target_date','—')} — {m.get('name','')}")
        else:
            lines.append("**Milestones:** none in Linear")
        lines.append("")
        if p.blockers:
            lines.append("**Blockers:**")
            for b in p.blockers[:3]:
                lines.append(f"- {b}")
            lines.append("")
        if p.health_signals:
            lines.append("**Risks & signals:**")
            for b in p.health_signals[:3]:
                lines.append(f"- {b}")
            lines.append("")
        if p.meeting_signal:
            lines.append(f"**From meetings:** _{p.meeting_signal}_")
            lines.append("")
        if p.week_delta:
            lines.append(f"**This week:** {p.week_delta}")
            for item in done_bullets:
                lines.append(f"- {item}")
            lines.append("")
        elif done_bullets:
            lines.append("**This week:**")
            for item in done_bullets:
                lines.append(f"- {item}")
            lines.append("")
        if p.next_week:
            lines.append(f"**Next week:** {p.next_week}")
            for item in next_bullets:
                if item != p.next_week:
                    lines.append(f"- {item}")
            lines.append("")
        elif next_bullets:
            lines.append("**Next week:**")
            for item in next_bullets:
                lines.append(f"- {item}")
            lines.append("")
    if on_track_projects:
        lines.append("## On Track")
        lines.append("")
        for p in on_track_projects:
            done_b, next_b = _project_activity_bullets({
                "delivered_bullets": p.delivered_bullets,
                "planned_bullets": p.planned_bullets,
                "linear_signals": {"completed": p.linear_signals.completed, "in_progress": p.linear_signals.in_progress, "todo": p.linear_signals.todo},
                "commit_signals": {"commits_this_week": p.commit_signals.commits_this_week, "active_repos": p.commit_signals.active_repos, "quiet_repos": p.commit_signals.quiet_repos},
                "issue_signals": {"stale_count": p.issue_signals.stale_count, "top_stale": p.issue_signals.top_stale, "backlog_growth": p.issue_signals.backlog_growth, "unowned_count": p.issue_signals.unowned_count, "blocked_threads": p.issue_signals.blocked_threads, "top_blocked": p.issue_signals.top_blocked},
                "milestones": p.milestones,
            })
            trend_disp = p.score_trend.display if p.score_trend and p.score_trend.display else ""
            score_str = f"{int(p.health_score)}/100" + (f" {trend_disp}" if trend_disp else "")
            target_str = (f" · {p.target_date}" if p.target_date else "") + (f" ({p.days_left}d)" if p.days_left is not None else "")
            lines.append(f"### {p.name}")
            lines.append(f"*On Track · {int(p.work_progress_pct)}% done · score {score_str}{target_str}*")
            lines.append("")
            if done_b:
                lines.append("**Delivered:**")
                for b in done_b[:4]:
                    lines.append(f"- {b}")
                lines.append("")
            if next_b:
                lines.append("**Next week:**")
                for b in next_b[:3]:
                    lines.append(f"- {b}")
                lines.append("")
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
    lines.append(f"*{t['COMPANY']} · signals: {', '.join(report.sources) or 'none'}*")
    if report.errors:
        lines.append(f"*Partial data: {'; '.join(report.errors)}*")

    return "\n".join(lines)
