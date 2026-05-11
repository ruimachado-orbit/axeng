#!/usr/bin/env python3
"""
Axeng — 1:1 Pre-read Generator
Fires as part of pre-meeting-brief.py when a meeting is identified as a 1:1.
Fetches: other person's commits, Linear issues, PRs, last 1:1 notes from Obsidian.
Produces suggested talking points.
"""
import json, os, subprocess, sys, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_FILE = HERMES_HOME / ".env"
TOKEN_PATH = HERMES_HOME / "google_token.json"
VAULT_PATH = Path.home() / "Documents" / "Obsidian Vault"

# ── Config (team-intel dir) ───────────────────────────────────────────────────
TEAM_INTEL_DIR = HERMES_HOME / "scripts" / "team-intel"
sys.path.insert(0, str(TEAM_INTEL_DIR))
try:
    from config import TEAM_MEMBERS, EX_MEMBERS, GITHUB_NAME_MAP, LINEAR_GITHUB_MAP, LINEAR_PROJECT_IDS
except ImportError:
    TEAM_MEMBERS = []

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_env() -> dict:
    out = {}
    if ENV_FILE.exists():
        for ln in ENV_FILE.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.strip().split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def load_google_token() -> str:
    if TOKEN_PATH.exists():
        try:
            data = json.loads(TOKEN_PATH.read_text())
            return data.get("token") or data.get("access_token") or ""
        except Exception:
            pass
    return ""

# ── Parse 1:1 attendee from meeting title or attendees ─────────────────────────
def parse_1on1_person(title: str, attendees: list) -> Optional[dict]:
    """Return {'name': '...', 'github': '...', 'email': '...'} for the non-self person."""
    # Known team members by name pattern
    team_names = {
        "daniel": "Daniel Almeida", "pedro": "Pedro Ferreira",
        "diogo": "Diogo Oliveira", "rikkarth": "Rikkarth R.",
        "anastasiia": "Anastasiia Mishchenko", "joão": "João FCSantos", "joao": "João FCSantos",
        "luis": "Luis Santos",
    }
    # Try to extract name from title like "1:1 with Pedro" or "Pedro 1:1"
    title_lower = title.lower()
    for key, full_name in team_names.items():
        if key in title_lower:
            # Find it in TEAM_MEMBERS
            for m in TEAM_MEMBERS:
                if m.get("name") == full_name:
                    return m

    # Fall back to first attendee who's not Rui
    env = load_env()
    self_email = env.get("USER_EMAIL", "user@example.com").lower()
    for a in attendees:
        email = (a.get("email") or "").lower()
        if email and email != self_email and "@" in email:
            # Match to team member by email
            for m in TEAM_MEMBERS:
                if m.get("email", "").lower() == email:
                    return m
            # Unknown external — return basic info
            return {
                "name": a.get("displayName") or a.get("email", "").split("@")[0],
                "github": "",
                "email": email,
            }
    return None

# ── GitHub: recent commits for a person ──────────────────────────────────────
def fetch_person_commits(github_handle: str) -> list:
    if not github_handle:
        return []
    commits = []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    for org in ["OrbitPlatform", "Maio-Labs", "Maio-Labs-Secret-Sauce", "ruimachado-orbit"]:
        try:
            raw = subprocess.check_output(
                f'gh api repos/{org}/*/commits --paginate -f author="{github_handle}" -f since="{cutoff}"',
                shell=True, stderr=subprocess.DEVNULL, timeout=30
            )
            for c in json.loads(raw):
                commits.append({
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\n")[0][:70],
                    "date": c["commit"]["author"]["date"],
                    "repo": c["repository"]["nameWithOwner"],
                })
        except Exception:
            pass
    return commits

# ── GitHub: PRs authored waiting for review ──────────────────────────────────
def fetch_person_pending_prs(github_handle: str) -> list:
    if not github_handle:
        return []
    results = []
    try:
        raw = subprocess.check_output(
            f'gh search prs --author={github_handle} --state=open --limit=10 --json number,title,repository,url,updatedAt,reviewRequests',
            shell=True, stderr=subprocess.DEVNULL, timeout=20
        )
        prs = json.loads(raw)
        for pr in prs:
            age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(pr["updatedAt"].replace("Z", "+00:00"))).days
            reviewers = pr.get("reviewRequests") or []
            results.append({
                "repo": pr["repository"]["nameWithOwner"],
                "number": pr["number"],
                "title": pr["title"][:70],
                "age_days": age_days,
                "reviewers": len(reviewers),
            })
    except Exception:
        pass
    return results

# ── Linear: open issues assigned to person ───────────────────────────────────
def fetch_person_linear_issues(person_name: str) -> dict:
    env = load_env()
    key = env.get("LINEAR_API_KEY", "")
    if not key or not person_name:
        return {}

    # Try to find Linear user ID from name
    query = """
    query { users(first: 20) { nodes { id name email } } }
    """
    payload = json.dumps({"query": query}).encode()
    req = __import__("urllib.request").request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={"Authorization": key, "Content-Type": "application/json"},
    )
    try:
        with __import__("urllib.request").request.urlopen(req, timeout=15) as r:
            users = json.loads(r.read()).get("data", {}).get("users", {}).get("nodes", [])
        user_id = next((u["id"] for u in users if person_name.lower() in u.get("name", "").lower()), None)
    except Exception:
        return {}

    if not user_id:
        return {}

    # Fetch open issues assigned to this user
    gql = """
    query($assignee: String!) {
      issues(filter: { assignee: { id: { eq: $assignee } } }, first: 20) {
        nodes {
          title state { name } priority identifier
          updatedAt dueDate
          project { name }
        }
      }
    }
    """
    payload = json.dumps({"query": gql, "variables": {"assignee": user_id}}).encode()
    req = __import__("urllib.request").request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={"Authorization": key, "Content-Type": "application/json"},
    )
    try:
        with __import__("urllib.request").request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        issues = data.get("data", {}).get("issues", {}).get("nodes", [])
        open_issues = [i for i in issues if i.get("state", {}).get("name") not in ("completed", "canceled")]
        return {"open": open_issues, "total": len(open_issues)}
    except Exception:
        return {}

# ── Obsidian: last 1:1 notes for person ──────────────────────────────────────
def fetch_last_1on1_notes(person_name: str) -> list:
    """Search vault for notes mentioning the person (last 30 days)."""
    if not person_name:
        return []
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    notes = []
    vault = Path(VAULT_PATH)
    if not vault.exists():
        return []
    for md in vault.rglob("*.md"):
        try:
            # Check modified time
            mtime = datetime.fromtimestamp(md.stat().st_mtime)
            if mtime < datetime.now() - timedelta(days=30):
                continue
            content = md.read_text()
            if person_name.lower() in content.lower() and any(
                kw in content.lower() for kw in ["1:1", "1-1", "one-on-one", "sync", "catch-up"]
            ):
                # Extract snippet around person name
                idx = content.lower().index(person_name.lower())
                snippet = content[max(0, idx-50):idx+150]
                notes.append({
                    "file": md.name,
                    "date": mtime.strftime("%-d %b"),
                    "snippet": snippet.strip(),
                })
        except Exception:
            continue
    return sorted(notes, key=lambda n: n["date"], reverse=True)[:2]

# ── Sprint: rough velocity from Linear ───────────────────────────────────────
def fetch_sprint_velocity(person_name: str) -> dict:
    """Approximate sprint velocity: issues completed in last 2 weeks."""
    env = load_env()
    key = env.get("LINEAR_API_KEY", "")
    if not key or not person_name:
        return {}

    gql = """
    query($since: DateTime!) {
      issues(
        filter: {
          assignee: { name: { eq: "%s" } }
          state: { type: { eq: "completed" } }
          updatedAt: { gte: $since }
        }
        first: 20
      ) {
        nodes { title updatedAt project { name } }
      }
    }
    """ % person_name

    since = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    payload = json.dumps({"query": gql, "variables": {"since": since}}).encode()
    req = __import__("urllib.request").request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={"Authorization": key, "Content-Type": "application/json"},
    )
    try:
        with __import__("urllib.request").request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        issues = data.get("data", {}).get("issues", {}).get("nodes", []) or []
        by_project = {}
        for i in issues:
            p = i.get("project", {}).get("name", "Unknown")
            by_project[p] = by_project.get(p, 0) + 1
        return {"completed_14d": len(issues), "by_project": by_project}
    except Exception:
        return {}

# ── Build the pre-read ───────────────────────────────────────────────────────
def build_preread(person: dict, commits: list, prs: list, linear: dict,
                  last_notes: list, velocity: dict) -> str:
    name = person.get("name", "?")
    lines = []

    lines.append(f"📋 *1:1 Pre-read — {name}*\n")
    lines.append(f"Open Linear issues: *{linear.get('total', '?')}*")

    # ── Linear issues ──
    open_issues = linear.get("open", [])
    if open_issues:
        prio_map = {0: "🔴", 1: "🔴", 2: "🟠", 3: "🟡"}
        lines.append("\n*Linear — your open issues*")
        for i in open_issues[:6]:
            tag = prio_map.get(i.get("priority", 0), "⚪")
            proj = i.get("project", {}).get("name", "")
            due = i.get("dueDate", "")[:10]
            due_str = f" → {due}" if due else ""
            lines.append(f"{tag} `{i['identifier']}` {i['title'][:55]}{due_str}")
            if proj:
                lines.append(f"   └ {proj}")
    else:
        lines.append("\n*Linear* — no open issues assigned 🎉")

    # ── Recent commits ──
    if commits:
        lines.append(f"\n*GitHub ({len(commits)} commits this week)*")
        for c in commits[:4]:
            repo_short = c["repo"].split("/")[-1] if "/" in c["repo"] else c["repo"]
            lines.append(f"  • `{c['sha']}` {c['message'][:60]}")
    else:
        lines.append("\n*GitHub* — no commits this week")

    # ── Pending PRs ──
    if prs:
        lines.append(f"\n*Pending PRs ({len(prs)})*")
        for pr in prs[:3]:
            old_tag = "⚠️" if pr["age_days"] >= 3 else ""
            lines.append(f"{old_tag} `{pr['repo'].split('/')[-1]}#{pr['number']}` {pr['title']} ({pr['age_days']}d)")

    # ── Velocity ──
    if velocity:
        completed = velocity.get("completed_14d", 0)
        lines.append(f"\n*Velocity (14d)*: {completed} issues completed")
        by_proj = velocity.get("by_project", {})
        if by_proj:
            proj_lines = ", ".join(f"{p}: {n}" for p, n in sorted(by_proj.items(), key=lambda x: -x[1])[:3])
            lines.append(f"  └ {proj_lines}")

    # ── Last notes ──
    if last_notes:
        lines.append("\n*Previous 1:1 notes*")
        for n in last_notes:
            lines.append(f"  📝 [{n['date']}] {n['snippet'][:80]}")

    # ── Suggested talking points ──
    lines.append("\n*Talking points*")
    if open_issues and len(open_issues) > 3:
        lines.append("• Review priorities — you have " + str(len(open_issues)) + " open issues")
    if prs and any(p["age_days"] >= 3 for p in prs):
        lines.append("• Any PRs stuck waiting for review?")
    if last_notes:
        lines.append("• Follow up on action items from last sync")
    if not commits and open_issues:
        lines.append("• Curious what blocked progress this week?")
    if velocity and velocity.get("completed_14d", 0) == 0 and open_issues:
        lines.append("• Let's review what's on your plate — 0 issues closed in 2 weeks")
    lines.append("• Anything blocking you right now?")

    lines.append("\n_Axeng 1:1 pre-read · generated before your sync_")
    return "\n".join(lines)

# ── Telegram send ─────────────────────────────────────────────────────────────
def send_telegram(text: str):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_HOME_CHANNEL", "") or os.environ.get("TELEGRAM_HOME_CHANNEL", "")
    if not token or not chat_id:
        print("ERROR: Telegram creds not configured")
        return

    import urllib.parse, urllib.request
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "Markdown",
    }).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=15):
            pass
    except Exception as e:
        print(f"Telegram send failed: {e}")

# ── Public entry point ────────────────────────────────────────────────────────
def generate_1on1_preread(title: str, attendees: list, dry: bool = False) -> Optional[str]:
    """Main function called by pre-meeting-brief.py."""
    person = parse_1on1_person(title, attendees)
    if not person:
        return None

    github = person.get("github", "")
    name = person.get("name", "")

    commits = fetch_person_commits(github) if github else []
    prs = fetch_person_pending_prs(github) if github else []
    linear = fetch_person_linear_issues(name)
    last_notes = fetch_last_1on1_notes(name)
    velocity = fetch_sprint_velocity(name)

    pread = build_preread(person, commits, prs, linear, last_notes, velocity)
    if not dry:
        send_telegram(pread)
    return pread

# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="1:1 with Team")
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()

    # Parse person from title, no hardcoded attendees - let parse_1on1_person work from title
    attendees = []
    result = generate_1on1_preread(args.title, attendees, dry=args.dry)
    if result:
        print(result)
    else:
        print("No attendee found in title or attendees list.")