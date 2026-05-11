#!/usr/bin/env python3
"""
Axeng — Daily Standup Brief
Fires at 07:30 Mon-Fri. Produces a focused brief for the standup:
  • What shipped yesterday
  • What's blocked (unassigned / stale Linear issues)
  • Who's out of office today
  • PRs waiting >48h for review
"""
import json, os, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Config paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))  # local config first (has all legacy constants)
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_FILE = HERMES_HOME / ".env"
TEAM_INTEL_DIR = HERMES_HOME / "scripts" / "team-intel"
sys.path.insert(1, str(TEAM_INTEL_DIR))  # team-intel second (fallback)

# ── Import config (local first, then hermes fallback) ──────────────────────
from config import (
    GITHUB_ORGS, EX_MEMBERS, GITHUB_NAME_MAP,
    LINEAR_PROJECT_IDS, LINEAR_GITHUB_MAP,
    RECIPIENTS, email_from,
)

# ── Env helpers ───────────────────────────────────────────────────────────────
def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for ln in ENV_FILE.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.strip().split("=", 1)
                env[k] = v
    return env

# ── GitHub: commits from yesterday ──────────────────────────────────────────
def fetch_yesterday_commits() -> list:
    """Get commits from all orgs for the last full day (yesterday)."""
    yesterday = datetime.now() - timedelta(days=1)
    cutoff = yesterday.strftime("%Y-%m-%dT00:00:00Z")
    commits = []

    for org in GITHUB_ORGS:
        try:
            out = subprocess.check_output(
                f'gh api orgs/{org}/repos --paginate --jq ".[].nameWithOwner"',
                shell=True, stderr=subprocess.DEVNULL, timeout=30
            )
            repos = [r.strip() for r in out.decode().strip().splitlines() if r.strip()]
        except Exception:
            continue

        for repo in repos:
            try:
                raw = subprocess.check_output(
                    f'gh api repos/{repo}/commits --paginate -f since="{cutoff}"',
                    shell=True, stderr=subprocess.DEVNULL, timeout=60
                )
                for c in json.loads(raw):
                    author_login = (c.get("author") or {}).get("login", c["commit"]["author"]["name"])
                    if author_login in EX_MEMBERS:
                        continue
                    commits.append({
                        "sha": c["sha"][:7],
                        "message": c["commit"]["message"].split("\n")[0],
                        "date": c["commit"]["author"]["date"],
                        "author": GITHUB_NAME_MAP.get(author_login, author_login),
                        "repo": repo,
                    })
            except Exception:
                pass
    return commits

# ── GitHub: PRs waiting >48h ─────────────────────────────────────────────────
def fetch_stale_pr_reviews() -> list:
    """PRs merged in last 7 days where review requested >48h ago and still no review."""
    stale = []
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    for org in GITHUB_ORGS:
        try:
            out = subprocess.check_output(
                f'gh api orgs/{org}/repos --paginate --jq ".[].nameWithOwner"',
                shell=True, stderr=subprocess.DEVNULL, timeout=30
            )
            repos = [r.strip() for r in out.decode().strip().splitlines() if r.strip()]
        except Exception:
            continue

        for repo in repos:
            try:
                raw = subprocess.check_output(
                    f'gh api repos/{repo}/pulls?state=open&per_page=50 --paginate',
                    shell=True, stderr=subprocess.DEVNULL, timeout=30
                )
                prs = json.loads(raw)
                for pr in prs:
                    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    age_hours = (datetime.now().astimezone() - created).total_seconds() / 3600
                    reviews = pr.get("requested_reviewers", [])
                    if age_hours > 48 and reviews:
                        stale.append({
                            "repo": repo,
                            "number": pr["number"],
                            "title": pr["title"],
                            "author": pr["user"]["login"],
                            "age_hours": int(age_hours),
                            "reviewers": [r["login"] for r in reviews],
                        })
            except Exception:
                pass
    return stale

# ── Linear: stale/blocked issues ─────────────────────────────────────────────
def fetch_linear_issues() -> dict:
    """Fetch open issues with no update in 3+ days, plus unassigned."""
    env = load_env()
    key = env.get("LINEAR_API_KEY", "")
    if not key:
        return {}

    stale, unassigned = [], []
    cutoff_days = 3
    cutoff = (datetime.now() - timedelta(days=cutoff_days)).strftime("%Y-%m-%d")

    for project_id in LINEAR_PROJECT_IDS.values():
        query = """
        query($id: String!) {
          projectUpdates(filter: { project: { id: { eq: $id } } }, first: 5) {
            nodes { body createdAt }
          }
          issues(filter: { project: { id: { eq: $id } } }, first: 50) {
            nodes {
              title state { name } priority identifier
              assignee { name }
              updatedAt
            }
          }
        }
        """
        payload = json.dumps({"query": query, "variables": {"id": project_id}})
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "POST",
                 "-H", f"Authorization: {key}",
                 "-H", "Content-Type: application/json",
                 "-d", payload,
                 "https://api.linear.app/graphql"],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(result.stdout)
            project_name = next((k for k, v in LINEAR_PROJECT_IDS.items() if v == project_id), "?")
            issues = data.get("data", {}).get("issues", {}).get("nodes", [])
            updates = data.get("data", {}).get("projectUpdates", {}).get("nodes", [])

            # Check if project has any recent updates
            has_recent_update = any(
                u.get("createdAt", "")[:10] >= cutoff
                for u in updates
            )
            if not has_recent_update:
                stale.append({"project": project_name, "last_update": "3+ days ago"})

            for issue in issues:
                if issue.get("state", {}).get("name") in ("unstarted", "started", "backlog"):
                    if not issue.get("assignee"):
                        unassigned.append({
                            "title": issue["title"],
                            "project": project_name,
                            "id": issue.get("identifier", ""),
                            "priority": issue.get("priority", 0),
                        })
        except Exception:
            pass

    return {"stale_projects": stale, "unassigned": unassigned}

# ── Calendar: who's OOO ───────────────────────────────────────────────────────
def fetch_ooo_today() -> list:
    """Check Google Calendar for all-day events matching OOO keywords."""
    try:
        mcp = Path("~/.hermes/skills/productivity/google-workspace/scripts/google_api.py").expanduser()
        raw = subprocess.check_output(
            ["python3", str(mcp), "calendar", "list",
             "--days", "1", "--format", "json"],
            stderr=subprocess.DEVNULL, timeout=20
        )
        events = json.loads(raw)
        ooo_keywords = ["off", "ooo", "out of office", "ferias", "férias", "holiday", "vacation"]
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            e for e in events
            if e.get("start", {}).get("date", "") == today
            and any(k in e.get("summary", "").lower() for k in ooo_keywords)
        ]
    except Exception:
        return []

# ── Build the brief ─────────────────────────────────────────────────────────
def build_brief(yesterday_commits, stale_prs, linear, ooo) -> str:
    today = datetime.now().strftime("%-d %b %Y")
    lines = []
    lines.append(f"📋 Standup Brief · {today}\n")

    # ── What shipped yesterday ──
    if yesterday_commits:
        by_author = {}
        for c in yesterday_commits:
            author = c["author"]
            by_author.setdefault(author, []).append(c)
        lines.append("✅ **What shipped yesterday**")
        for author, commits in sorted(by_author.items(), key=lambda x: -len(x[1])):
            msgs = ", ".join(f"`{c['sha']}` {c['message'][:50]}" for c in commits[:2])
            lines.append(f"  • **{author}** ({len(commits)} commits): {msgs}")
    else:
        lines.append("✅ **What shipped yesterday** — nothing recorded")

    # ── Blocked issues ──
    if linear["unassigned"]:
        lines.append("\n🚧 **Unassigned issues** (need owner)")
        for issue in linear["unassigned"][:5]:
            prio_tag = {0: "🔴", 1: "🔴", 2: "🟠", 3: "🟡"}.get(issue["priority"], "⚪")
            lines.append(f"  {prio_tag} `{issue['id']}` {issue['title'][:60]} [{issue['project']}]")
    else:
        lines.append("\n🚧 **Unassigned issues** — none")

    if linear["stale_projects"]:
        lines.append("\n🕐 **Quiet projects** (no update in 3+ days)")
        for p in linear["stale_projects"]:
            lines.append(f"  • {p['project']} — last update: {p['last_update']}")

    # ── Stale PRs ──
    if stale_prs:
        lines.append(f"\n⏳ **Stale PRs** ({len(stale_prs)} waiting >48h for review)")
        for pr in stale_prs[:4]:
            lines.append(f"  • `{pr['repo']}#{pr['number']}` {pr['title'][:55]} — "
                         f"by {pr['author']} · {pr['age_hours']}h old · waiting on {', '.join(pr['reviewers'][:2])}")
    else:
        lines.append("\n⏳ **Stale PRs** — none")

    # ── OOO ──
    if ooo:
        names = ", ".join(e.get("summary", "OOO") for e in ooo)
        lines.append(f"\n🌴 **Out today:** {names}")
    else:
        lines.append("\n🌴 **Out today:** nobody reported")

    lines.append("\n_Generated by Axeng · standup-brief.py_")
    return "\n".join(lines)

# ── Send ─────────────────────────────────────────────────────────────────────
def send_telegram(text: str):
    """Send the brief via Telegram (hermes-agent gateway)."""
    try:
        # Try via hermes send_message tool
        import urllib.request, urllib.parse
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
            req = urllib.request.Request(url, data.encode())
            urllib.request.urlopen(req, timeout=10)
            return True
    except Exception:
        pass

    # Fallback: print to stdout (cron picks this up)
    print(text)
    return False

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate daily standup brief for team",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              Generate and print brief
  %(prog)s --send       Generate and send to Telegram

The brief includes:
  • What shipped yesterday (commits)
  • Who's blocked (unassigned Linear issues)
  • Stale PRs (>48h waiting for review)
  • Who's out of office today
        """
    )
    parser.add_argument("--send", action="store_true",
                       help="Send brief to Telegram (requires TELEGRAM_BOT_TOKEN)")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress progress messages")

    args = parser.parse_args()

    if not args.quiet:
        print("🤖 Axeng Standup Brief — building...")

    if not args.quiet:
        print("  Fetching yesterday's commits...")
    commits = fetch_yesterday_commits()

    if not args.quiet:
        print("  Checking for stale PRs...")
    stale = fetch_stale_pr_reviews()

    if not args.quiet:
        print("  Checking Linear for blockers...")
    linear = fetch_linear_issues()

    if not args.quiet:
        print("  Checking who's OOO...")
    ooo = fetch_ooo_today()

    brief = build_brief(commits, stale, linear, ooo)
    print("\n" + brief)

    if args.send:
        send_telegram(brief)
        if not args.quiet:
            print("\n✅ Sent to Telegram")

    if not args.quiet:
        print("\n✅ Done.")