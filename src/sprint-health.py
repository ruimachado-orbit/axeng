#!/usr/bin/env python3
"""
Axeng — Sprint Health Score
Runs weekly (Friday before the report) or on-demand.
Produces a sprint health dashboard:
  • Velocity vs. last sprint (Linear issues completed)
  • Scope creep: issues added mid-sprint
  • At-risk items: no updates in 5+ days
  • Burn chart estimate (issues open vs. closed)
"""
import json, os, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))  # local config first (has all legacy constants)
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_FILE = HERMES_HOME / ".env"
TEAM_INTEL_DIR = HERMES_HOME / "scripts" / "team-intel"
sys.path.insert(1, str(TEAM_INTEL_DIR))  # hermes fallback second

try:
    from config import LINEAR_PROJECT_IDS, LINEAR_GITHUB_MAP, TEAM_MEMBERS
except ImportError:
    LINEAR_PROJECT_IDS = {}
    LINEAR_GITHUB_MAP = {}
    TEAM_MEMBERS = []

# ── Env ──────────────────────────────────────────────────────────────────────
def load_env() -> dict:
    out = {}
    if ENV_FILE.exists():
        for ln in ENV_FILE.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.strip().split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out

# ── Linear GraphQL helper ────────────────────────────────────────────────────
def linear_query(query: str, variables: dict = None) -> dict:
    env = load_env()
    key = env.get("LINEAR_API_KEY", "")
    if not key:
        return {"errors": [{"message": "LINEAR_API_KEY not set"}]}

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    body = json.dumps(payload).encode()
    # Use top-level import (Python 3.9 compat: urllib.request.Request, not .request.request)
    import urllib.request
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers={"Authorization": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"errors": [{"message": str(e)}]}


def fetch_project_health(project_id: str, project_name: str) -> dict:
    """Fetch all issues + updates for a project, return health data."""
    query = """
    query($id: String!) {
      project(id: $id) {
        name
        issues(first: 100) {
          nodes {
            title state { name type } priority identifier
            updatedAt createdAt dueDate
            assignee { name }
          }
        }
      }
    }
    """
    data = linear_query(query, {"id": project_id})
    if "errors" in data:
        return {}

    project = (data.get("data") or {}).get("project") or {}
    issues_raw = project.get("issues", {}).get("nodes", [])
    updates = []

    # Classify by state type
    state_types = {}
    for i in issues_raw:
        st = i.get("state", {}) or {}
        t = st.get("type", "unset")
        state_types[t] = state_types.get(t, 0) + 1

    total = len(issues_raw)
    completed = state_types.get("completed", 0)
    canceled = state_types.get("canceled", 0)
    active = state_types.get("started", 0) + state_types.get("unstarted", 0)
    backlog = state_types.get("backlog", 0)

    # Scope creep: issues created in last 7 days
    last_7d = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    created_recently = sum(
        1 for i in issues_raw
        if (i.get("createdAt", "")[:10]) >= last_7d
    )

    # Stale: no update in 5+ days
    cutoff_5d = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")
    stale = [
        i for i in issues_raw
        if i.get("state", {}).get("type") in ("started", "unstarted")
        and (i.get("updatedAt", "")[:10]) < cutoff_5d
    ]

    # At-risk: started + no assignee
    at_risk = [
        i for i in issues_raw
        if i.get("state", {}).get("type") == "started"
        and not i.get("assignee")
    ]

    # Last project update
    last_update = updates[0].get("createdAt", "") if updates else ""
    if last_update:
        days_since_update = (datetime.now(timezone.utc) - datetime.fromisoformat(last_update.replace("Z", "+00:00"))).days
    else:
        days_since_update = 99

    # Velocity: completed in last 14 days
    cutoff_14d = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
    velocity_14d = sum(
        1 for i in issues_raw
        if i.get("state", {}).get("type") == "completed"
        and (i.get("updatedAt", "")[:10]) >= cutoff_14d
    )

    return {
        "name": project_name,
        "total": total,
        "completed": completed,
        "canceled": canceled,
        "active": active,
        "backlog": backlog,
        "velocity_14d": velocity_14d,
        "created_recently": created_recently,
        "stale": stale,
        "at_risk": at_risk,
        "days_since_update": 0,  # projectUpdates filter unavailable in Linear API
        "updates": updates,
    }


def calculate_sprint_burn(health: list) -> dict:
    """
    Estimate burn rate: closed vs. total (excl. cancelled).
    A healthy sprint should be burning down towards zero active issues.
    """
    total_active = sum(h["active"] for h in health)
    total_completed = sum(h["completed"] for h in health)
    total = sum(h["total"] for h in health)
    if total == 0:
        return {"burn_pct": 0, "healthy": True}

    # Burn = completed / (completed + active + backlog)
    denominator = total - sum(h["canceled"] for h in health)
    burn_pct = int(total_completed / denominator * 100) if denominator > 0 else 0

    # Healthy: burn > 30% for mid-sprint, or project is nearly done
    healthy = burn_pct >= 30 or total_completed > total_active

    return {"burn_pct": burn_pct, "healthy": healthy,
            "total_completed": total_completed, "total_active": total_active}


def score_project(health: dict) -> tuple:
    """
    Health score 0-100 for a project.
    Deductions: no recent update, stale issues, at-risk, scope creep.
    """
    score = 100
    reasons = []

    if health["days_since_update"] >= 5:
        score -= 20
        reasons.append(f"No update in {health['days_since_update']}d")

    if len(health["stale"]) >= 3:
        score -= 15
        reasons.append(f"{len(health['stale'])} stale issues")
    elif len(health["stale"]) >= 1:
        score -= 8
        reasons.append(f"{len(health['stale'])} stale issue(s)")

    if len(health["at_risk"]) >= 2:
        score -= 15
        reasons.append(f"{len(health['at_risk'])} at-risk (started + no owner)")
    elif len(health["at_risk"]) >= 1:
        score -= 8

    if health["created_recently"] >= 5:
        score -= 10
        reasons.append(f"Scope creep: {health['created_recently']} issues added this week")
    elif health["created_recently"] >= 3:
        score -= 5

    if health["active"] > 15:
        score -= 10
        reasons.append(f"Heavy load: {health['active']} in-progress")

    return max(0, score), reasons


def build_health_card(health: dict, score: int, reasons: list) -> str:
    name = health["name"]
    badge_color = "#16a34a" if score >= 80 else "#f59e0b" if score >= 60 else "#dc2626"

    # State bar
    total = health["total"] or 1
    done_w = int(health["completed"] / total * 100)
    cancel_w = int(health["canceled"] / total * 100)
    active_w = int(health["active"] / total * 100)
    backlog_w = 100 - done_w - cancel_w - active_w

    state_bar = (
        f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin:8px 0;">'
        f'<div style="width:{done_w}%;background:#16a34a;" title="Completed {health["completed"]}"></div>'
        f'<div style="width:{cancel_w}%;background:#9ca3af;" title="Cancelled {health["canceled"]}"></div>'
        f'<div style="width:{active_w}%;background:#2563eb;" title="Active {health["active"]}"></div>'
        f'<div style="width:{max(0,backlog_w)}%;background:#f3f4f6;" title="Backlog {health["backlog"]}"></div>'
        f'</div>'
        f'<div style="display:flex;gap:6px;font-size:10px;color:#888;">'
        f'<span style="color:#16a34a">■ {health["completed"]} done</span>'
        f'<span style="color:#2563eb">■ {health["active"]} active</span>'
        f'<span style="color:#6b7280">■ {health["backlog"]} backlog</span>'
        f'</div>'
    )

    reason_html = ""
    if reasons:
        reason_html = (
            '<div style="margin-top:8px;font-size:11px;color:#dc2626;">'
            + "".join(f'<span style="background:#fef2f2;padding:2px 6px;border-radius:4px;margin-right:4px;">⚠️ {r}</span>'
                      for r in reasons)
            + '</div>'
        )

    update_tag = ""
    if health["days_since_update"] >= 7:
        update_tag = '<span style="background:#fef2f2;color:#dc2626;font-size:10px;font-weight:600;padding:2px 6px;border-radius:4px;">❌ Silent 7+ days</span>'
    elif health["days_since_update"] >= 3:
        update_tag = '<span style="background:#fffbeb;color:#d97706;font-size:10px;font-weight:600;padding:2px 6px;border-radius:4px;">⚠️ No update 3d</span>'

    return f"""
<div style="background:#fff;border-radius:12px;padding:16px;margin-bottom:10px;border:1px solid #e5e7eb;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div style="font-size:12px;font-weight:700;color:#000;">{name}</div>
      <div style="font-size:11px;color:#888;margin-top:2px;">{health["total"]} issues · {health["velocity_14d"]} closed (14d)</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:22px;font-weight:800;color:{badge_color};">{score}</div>
      <div style="font-size:10px;color:#888;">health score</div>
    </div>
  </div>
  {state_bar}
  {reason_html}
  <div style="margin-top:6px;display:flex;gap:6px;align-items:center;">
    {update_tag}
    {" "}
  </div>
</div>"""


def build_html(health_list: list) -> str:
    total_score = sum(s for s, _ in [score_project(h) for h in health_list]) / len(health_list) if health_list else 0

    overall_badge = (
        "#16a34a" if total_score >= 80
        else "#f59e0b" if total_score >= 60
        else "#dc2626"
    )

    burn = calculate_sprint_burn(health_list)

    today = datetime.now().strftime("%-d %b %Y")

    project_cards = ""
    for h in health_list:
        score, reasons = score_project(h)
        project_cards += build_health_card(h, score, reasons)

    # Stale issues across all projects
    all_stale = []
    for h in health_list:
        for i in h["stale"]:
            all_stale.append({
                "title": i.get("title", "?")[:60],
                "project": h["name"],
                "id": i.get("identifier", ""),
                "days": 5,
            })

    stale_section = ""
    if all_stale:
        stale_section = f"""
<div style="margin-top:24px;">
  <div style="font-size:11px;font-weight:600;color:#999;letter-spacing:.5px;text-transform:uppercase;margin-bottom:8px;">
    ⚠️ Stale Issues ({len(all_stale)} — no update in 5+ days)
  </div>
  {''.join(f'<div style="background:#fff;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">'
           f'<span style="font-size:12px;">`{s["id"]}` {s["title"]}</span>'
           f'<span style="font-size:11px;color:#888;">{s["project"]}</span>'
           f'</div>' for s in all_stale[:8])}
</div>"""

    # Scope creep section
    scope_creep = [(h["name"], h["created_recently"]) for h in health_list if h["created_recently"] >= 3]
    creep_section = ""
    if scope_creep:
        creep_section = f"""
<div style="margin-top:16px;">
  <div style="font-size:11px;font-weight:600;color:#999;letter-spacing:.5px;text-transform:uppercase;margin-bottom:8px;">
    📈 Scope Creep (issues added this week)
  </div>
  {''.join(f'<div style="display:flex;justify-content:space-between;padding:8px 12px;background:#fff;border-radius:8px;margin-bottom:4px;">'
           f'<span style="font-size:12px;font-weight:600;">{name}</span>'
           f'<span style="font-size:12px;color:#dc2626;font-weight:700;">+{n} issues</span></div>'
           for name, n in sorted(scope_creep, key=lambda x: -x[1]))}
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sprint Health</title></head>
<body style="margin:0;padding:24px;background:#f7f7f7;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
<div style="max-width:640px;margin:0 auto;">

  <div style="margin-bottom:20px;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
      <div style="width:28px;height:28px;background:#000;border-radius:6px;display:flex;align-items:center;justify-content:center;">
        <span style="color:#d4ff00;font-size:14px;font-weight:800;">M</span>
      </div>
      <span style="font-size:12px;font-weight:600;color:#666;">MAIO LABS</span>
    </div>
    <h1 style="margin:0;font-size:28px;font-weight:800;color:#000;letter-spacing:-1px;">Sprint Health</h1>
    <p style="margin:4px 0 0;font-size:13px;color:#666;">{today} · {len(health_list)} projects tracked</p>
  </div>

  <!-- Overall score -->
  <div style="background:#fff;border-radius:16px;padding:20px;margin-bottom:20px;text-align:center;">
    <div style="font-size:48px;font-weight:800;color:{overall_badge};">{int(total_score)}</div>
    <div style="font-size:12px;color:#888;margin-top:4px;">overall health score</div>
    <div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
      <div style="background:#f0fdf4;border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:20px;font-weight:800;color:#16a34a;">{sum(h["completed"] for h in health_list)}</div>
        <div style="font-size:10px;color:#666;margin-top:2px;">completed</div>
      </div>
      <div style="background:#eff6ff;border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:20px;font-weight:800;color:#2563eb;">{sum(h["active"] for h in health_list)}</div>
        <div style="font-size:10px;color:#666;margin-top:2px;">in-progress</div>
      </div>
      <div style="background:#fff7ed;border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:20px;font-weight:800;color:#f59e0b;">{burn["burn_pct"]}%</div>
        <div style="font-size:10px;color:#666;margin-top:2px;">burn rate</div>
      </div>
    </div>
  </div>

  {creep_section}
  {stale_section}

  <!-- Per-project cards -->
  <div style="margin-top:16px;">
    <div style="font-size:11px;font-weight:600;color:#999;letter-spacing:.5px;text-transform:uppercase;margin-bottom:10px;">
      Project Health
    </div>
    {project_cards or '<p style="color:#aaa;font-size:13px;">No project data available.</p>'}
  </div>

  <div style="text-align:center;padding:16px 0;">
    <p style="margin:0;font-size:11px;color:#bbb;">Axeng · Sprint Health · {today} · Lisboa</p>
  </div>

</div>
</body>
</html>"""


def send_telegram(text: str):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_HOME_CHANNEL", "") or os.environ.get("TELEGRAM_HOME_CHANNEL", "")
    if not token or not chat_id:
        print("Telegram not configured — printing instead:")
        print(text)
        return

    import urllib.parse, urllib.request
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=15):
            pass
    except Exception as e:
        print(f"Telegram send failed: {e}")


def build_summary_md(health_list: list) -> str:
    """Plain text summary for Telegram / stdout."""
    total_score = sum(s for s, _ in [score_project(h) for h in health_list]) / len(health_list) if health_list else 0

    lines = [f"📊 *Sprint Health* · {datetime.now().strftime('%-d %b %Y')}\n"]

    badge = "🟢" if total_score >= 80 else "🟡" if total_score >= 60 else "🔴"
    lines.append(f"Overall: *{int(total_score)}/100* {badge}\n")

    lines.append("*By project:*")
    for h in sorted(health_list, key=lambda x: -score_project(x)[0]):
        s, reasons = score_project(h)
        icon = "🟢" if s >= 80 else "🟡" if s >= 60 else "🔴"
        creep_tag = f" 📈+{h['created_recently']}" if h["created_recently"] >= 3 else ""
        silent_tag = f" 😶{h['days_since_update']}d" if h["days_since_update"] >= 5 else ""
        stale_tag = f" ⚠️{len(h['stale'])}" if h["stale"] else ""
        lines.append(f"{icon} *{h['name']}* `{s}` · {h['completed']} done · {h['active']} active{creep_tag}{silent_tag}{stale_tag}")
        if reasons:
            for r in reasons[:2]:
                lines.append(f"   └ {r}")

    if sum(h["velocity_14d"] for h in health_list) == 0:
        lines.append("\n⚠️ *No issues closed in 14 days* — check progress")

    lines.append("\n_Axeng sprint-health.py_")
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", action="store_true", help="Output HTML report")
    parser.add_argument("--save", action="store_true", help="Save to reports/")
    parser.add_argument("--dry", action="store_true", help="Print only, no Telegram")
    args = parser.parse_args()

    print("📊 Sprint Health — running...")

    health_list = []
    for project_name, project_id in LINEAR_PROJECT_IDS.items():
        h = fetch_project_health(project_id, project_name)
        if h:
            health_list.append(h)

    print(f"   Checked {len(health_list)} projects")

    # Summary (text)
    summary = build_summary_md(health_list)
    print("\n" + summary)

    if not args.dry:
        send_telegram(summary)

    if args.html or args.save:
        html = build_html(health_list)
        if args.save:
            out_dir = Path.home() / ".hermes" / "scripts" / "team-intel" / "reports"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f"sprint-health-{datetime.now().strftime('%Y-%m-%d')}.html"
            path.write_text(html)
            print(f"\n   Saved: {path}")

    print("\n✅ Done.")