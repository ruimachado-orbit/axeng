#!/usr/bin/env python3
"""
Axeng — Daily Standup Brief
Fires at 07:30 Mon-Fri. Produces a focused brief for the standup:
  • What shipped yesterday
  • What's blocked (unassigned / stale Linear issues)
  • Who's out of office today
  • PRs waiting >48h for review
"""
import json, os, re, subprocess, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# ── Config paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))  # local config first (has all legacy constants)
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".axeng")))
ENV_FILE = HERMES_HOME / ".env"
TEAM_INTEL_DIR = HERMES_HOME / "scripts" / "team-intel"
sys.path.insert(1, str(TEAM_INTEL_DIR))  # team-intel second (fallback)

# ── Import config (local first, then hermes fallback) ──────────────────────
from config import (
    GITHUB_ORGS, GITHUB_REPOS, EX_MEMBERS, GITHUB_NAME_MAP,
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

# ── GitHub: shipped work from yesterday ──────────────────────────────────────
def yesterday_window():
    """Return yesterday's Lisbon date and UTC API bounds for the full local day."""
    tz = ZoneInfo("Europe/Lisbon")
    today = datetime.now(tz).date()
    yday = today - timedelta(days=1)
    start_local = datetime(yday.year, yday.month, yday.day, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (
        yday.isoformat(),
        start_local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        end_local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def gh_json(args: list, timeout: int = 45):
    raw = subprocess.check_output(["gh", "api", *args], stderr=subprocess.DEVNULL, timeout=timeout)
    return json.loads(raw.decode() or "{}")


def fetch_repos() -> list:
    """Resolve configured GitHub orgs/users to full repo names."""
    repos = list(GITHUB_REPOS or [])
    for owner in GITHUB_ORGS:
        for endpoint in (f"orgs/{owner}/repos", f"users/{owner}/repos"):
            try:
                data = gh_json(["-X", "GET", endpoint, "--paginate", "-f", "per_page=100"], timeout=30)
                repos.extend(r.get("full_name") for r in data if r.get("full_name"))
                break
            except Exception:
                continue
    return sorted(set(r for r in repos if r))


def fetch_merged_prs_yesterday() -> list:
    """Fetch PRs merged yesterday. This is the primary source for 'what shipped'."""
    yday, _, _ = yesterday_window()
    shipped = []
    seen = set()

    # Search per owner first: faster than per-repo and includes private repos with gh auth.
    for owner in GITHUB_ORGS:
        for qualifier in (f"org:{owner}", f"user:{owner}"):
            query = f"{qualifier} is:pr is:merged merged:{yday} archived:false"
            try:
                data = gh_json(["-X", "GET", "search/issues", "-f", f"q={query}", "-f", "per_page=100"], timeout=45)
                items = data.get("items", []) if isinstance(data, dict) else []
                if items:
                    for pr in items:
                        repo = pr.get("repository_url", "").split("/repos/")[-1]
                        key = (repo, pr.get("number"))
                        author_login = (pr.get("user") or {}).get("login", "")
                        if key in seen or author_login in EX_MEMBERS:
                            continue
                        seen.add(key)
                        shipped.append({
                            "repo": repo,
                            "number": pr.get("number"),
                            "title": pr.get("title", ""),
                            "author": GITHUB_NAME_MAP.get(author_login, author_login),
                            "url": pr.get("html_url", ""),
                            "closed_at": pr.get("closed_at", ""),
                        })
                    break
            except Exception:
                continue
    return sorted(shipped, key=lambda p: (p.get("repo", ""), p.get("number") or 0))


def fetch_yesterday_commits() -> list:
    """Get direct commits from yesterday as fallback/extra signal for shipped work."""
    _, since, until = yesterday_window()
    commits = []

    for repo in fetch_repos():
        try:
            data = gh_json(["-X", "GET", f"repos/{repo}/commits", "--paginate", "-f", f"since={since}", "-f", f"until={until}", "-f", "per_page=100"], timeout=45)
            for c in data if isinstance(data, list) else []:
                author_login = (c.get("author") or {}).get("login") or c["commit"]["author"].get("name", "")
                if author_login in EX_MEMBERS:
                    continue
                commits.append({
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\n")[0],
                    "date": c["commit"]["author"].get("date", ""),
                    "author": GITHUB_NAME_MAP.get(author_login, author_login),
                    "repo": repo,
                })
        except Exception:
            pass
    return commits

# ── GitHub: PRs waiting >48h ─────────────────────────────────────────────────
def fetch_stale_pr_reviews() -> list:
    """Open PRs waiting >48h with requested reviewers still pending."""
    stale = []

    for repo in fetch_repos():
        try:
            prs = gh_json(["-X", "GET", f"repos/{repo}/pulls", "--paginate", "-f", "state=open", "-f", "per_page=50"], timeout=30)
            for pr in prs if isinstance(prs, list) else []:
                created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
                reviews = pr.get("requested_reviewers", [])
                if age_hours > 48 and reviews:
                    stale.append({
                        "repo": repo,
                        "number": pr["number"],
                        "title": pr["title"],
                        "author": GITHUB_NAME_MAP.get(pr["user"]["login"], pr["user"]["login"]),
                        "age_hours": int(age_hours),
                        "reviewers": [GITHUB_NAME_MAP.get(r["login"], r["login"]) for r in reviews],
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
        mcp = Path("~/.axeng/skills/productivity/google-workspace/scripts/google_api.py").expanduser()
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
def clean_work_title(title: str) -> str:
    """Turn conventional commit/PR titles into readable achievement snippets."""
    title = re.sub(r"^\s*(feat|fix|refactor|chore|docs|test|perf|ci|build|style)(\([^)]+\))?:\s*", "", title, flags=re.I)
    title = re.sub(r"^\s*(merge pull request|merge branch)\b.*", "merge/integration work", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" -—")
    return title[:85] or "shipped work"


def build_developer_achievements(shipped_prs, yesterday_commits) -> list:
    """Deterministic per-developer shipped summary; no LLM in scheduled path."""
    by_author = defaultdict(lambda: {"prs": [], "commits": [], "repos": set()})
    for pr in shipped_prs:
        author = pr.get("author") or "Unknown"
        by_author[author]["prs"].append(pr)
        if pr.get("repo"):
            by_author[author]["repos"].add(pr["repo"].split("/")[-1])
    for c in yesterday_commits:
        author = c.get("author") or "Unknown"
        by_author[author]["commits"].append(c)
        if c.get("repo"):
            by_author[author]["repos"].add(c["repo"].split("/")[-1])

    lines = []
    for author, data in sorted(by_author.items(), key=lambda x: (-(len(x[1]["prs"])), -(len(x[1]["commits"])), x[0])):
        snippets = []
        for pr in data["prs"][:3]:
            snippets.append(clean_work_title(pr.get("title", "")))
        if not snippets:
            for c in data["commits"][:3]:
                snippets.append(clean_work_title(c.get("message", "")))
        repo_text = ", ".join(sorted(data["repos"])[:3])
        more_repos = f" +{len(data['repos'])-3} repos" if len(data["repos"]) > 3 else ""
        counts = []
        if data["prs"]:
            counts.append(f"{len(data['prs'])} PR" + ("s" if len(data["prs"]) != 1 else ""))
        if data["commits"]:
            counts.append(f"{len(data['commits'])} commit" + ("s" if len(data["commits"]) != 1 else ""))
        summary = "; ".join(snippets[:3])
        lines.append(f"  • **{author}** ({', '.join(counts)} · {repo_text}{more_repos}): {summary}")
    return lines


def build_brief(shipped_prs, yesterday_commits, stale_prs, linear, ooo) -> str:
    today = datetime.now().strftime("%-d %b %Y")
    lines = []
    lines.append(f"📋 Standup Brief · {today}\n")

    # ── What shipped yesterday ──
    lines.append("✅ **What shipped yesterday**")
    if shipped_prs:
        by_repo = {}
        for pr in shipped_prs:
            by_repo.setdefault(pr["repo"], []).append(pr)
        for repo, prs in sorted(by_repo.items(), key=lambda x: -len(x[1])):
            examples = "; ".join(
                f"#{p['number']} {p['title'][:55]} — {p['author']}"
                for p in prs[:3]
            )
            suffix = f" (+{len(prs)-3} more)" if len(prs) > 3 else ""
            lines.append(f"  • **{repo}** ({len(prs)} merged PRs): {examples}{suffix}")
        if yesterday_commits:
            lines.append(f"  ↳ GitHub commit signal: {len(yesterday_commits)} commits across monitored repos")
    elif yesterday_commits:
        by_author = {}
        for c in yesterday_commits:
            author = c["author"]
            by_author.setdefault(author, []).append(c)
        for author, commits in sorted(by_author.items(), key=lambda x: -len(x[1])):
            msgs = ", ".join(f"`{c['repo'].split('/')[-1]}@{c['sha']}` {c['message'][:45]}" for c in commits[:2])
            lines.append(f"  • **{author}** ({len(commits)} direct commits): {msgs}")
    else:
        lines.append("  • Nothing recorded in GitHub")

    achievement_lines = build_developer_achievements(shipped_prs, yesterday_commits)
    if achievement_lines:
        lines.append("\n👤 **Per developer achievements**")
        lines.extend(achievement_lines[:8])
        if len(achievement_lines) > 8:
            lines.append(f"  • +{len(achievement_lines)-8} more developers with GitHub activity")

    # ── Blocked issues ──
    if linear.get("unassigned"):
        lines.append("\n🚧 **Unassigned issues** (need owner)")
        for issue in linear["unassigned"][:5]:
            prio_tag = {0: "🔴", 1: "🔴", 2: "🟠", 3: "🟡"}.get(issue["priority"], "⚪")
            lines.append(f"  {prio_tag} `{issue['id']}` {issue['title'][:60]} [{issue['project']}]")
    else:
        lines.append("\n🚧 **Unassigned issues** — none")

    if linear.get("stale_projects"):
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
    print("🤖 Axeng Standup Brief — building...")

    print("  Fetching yesterday's merged PRs...")
    shipped = fetch_merged_prs_yesterday()

    print("  Fetching yesterday's direct commits...")
    commits = fetch_yesterday_commits()

    print("  Checking for stale PRs...")
    stale = fetch_stale_pr_reviews()

    print("  Checking Linear for blockers...")
    linear = fetch_linear_issues()

    print("  Checking who's OOO...")
    ooo = fetch_ooo_today()

    brief = build_brief(shipped, commits, stale, linear, ooo)
    print("\n" + brief)

    send_telegram(brief)
    print("\n✅ Done.")