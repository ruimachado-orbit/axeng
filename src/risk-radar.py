#!/usr/bin/env python3
"""
Axeng — Risk Radar
Monitors for early-warning signals:
  • Repos with no commits in 10+ days (quiet projects)
  • Linear projects with >3 in-progress issues and no movement
  • Team members with >5 open issues and low throughput
  • PRs open >7 days with no review requests
  • Linear issues with due dates in the past

Runs weekly (Friday) and on-demand.
"""
import json, os, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))  # local config first (has all legacy constants)
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_FILE = HERMES_HOME / ".env"
TEAM_INTEL_DIR = HERMES_HOME / "scripts" / "team-intel"
sys.path.insert(1, str(TEAM_INTEL_DIR))  # hermes fallback second

try:
    from config import LINEAR_PROJECT_IDS, LINEAR_GITHUB_MAP, TEAM_MEMBERS, EX_MEMBERS, GITHUB_ORGS
except ImportError:
    LINEAR_PROJECT_IDS = {}
    LINEAR_GITHUB_MAP = {}
    TEAM_MEMBERS = []
    EX_MEMBERS = set()
    GITHUB_ORGS = []


def load_env() -> dict:
    out = {}
    if ENV_FILE.exists():
        for ln in ENV_FILE.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.strip().split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def linear_query(query: str, variables: dict = None) -> dict:
    env = load_env()
    key = env.get("LINEAR_API_KEY", "")
    if not key:
        return {"errors": [{"message": "LINEAR_API_KEY not set"}]}

    payload = {"query": query, "variables": variables} if variables else {"query": query}
    body = json.dumps(payload).encode()
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


# ── Signal 1: Quiet repos (no commits in 10+ days) ────────────────────────────
def fetch_quiet_repos(days_threshold: int = 10) -> list:
    """Find repos in configured orgs with no recent commits."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).strftime("%Y-%m-%d")
    quiet = []

    all_repos = set()
    for org in GITHUB_ORGS:
        try:
            raw = subprocess.check_output(
                f'gh api orgs/{org}/repos --paginate --jq ".[].nameWithOwner"',
                shell=True, stderr=subprocess.DEVNULL, timeout=20
            )
            for line in raw.decode().strip().splitlines():
                if line.strip():
                    all_repos.add(line.strip())
        except Exception:
            pass

    for repo in all_repos:
        try:
            raw = subprocess.check_output(
                f'gh api repos/{repo}/commits --paginate -f per_page=1',
                shell=True, stderr=subprocess.DEVNULL, timeout=15
            )
            commits = json.loads(raw)
            if not commits:
                quiet.append({"repo": repo, "last_commit": "never", "days": 999})
                continue
            last_date = commits[0].get("commit", {}).get("author", {}).get("date", "")
            if last_date:
                last_dt = datetime.fromisoformat(last_date.replace("Z", "+00:00"))
                days_ago = (datetime.now(timezone.utc) - last_dt).days
                if days_ago >= days_threshold:
                    quiet.append({
                        "repo": repo,
                        "last_commit": last_date[:10],
                        "days": days_ago,
                    })
        except Exception:
            # Repo may be empty or inaccessible
            quiet.append({"repo": repo, "last_commit": "unknown", "days": days_threshold + 1})

    quiet.sort(key=lambda x: -x["days"])
    return quiet


# ── Signal 2: Stalled projects (started + no update in 5+ days) ──────────────
def fetch_stalled_projects(days_threshold: int = 5) -> list:
    stalled = []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).strftime("%Y-%m-%d")

    for project_name, project_id in LINEAR_PROJECT_IDS.items():
        # Get project issues + updates
        query = """
        query($id: String!) {
          project(id: $id) {
            name
            issues(first: 100) {
              nodes {
                title state { name type } identifier
                updatedAt startedAt
                assignee { name }
              }
            }
          }
          projectUpdates(filter: { project: { id: { eq: $id } } }, first: 5, orderBy: { field: createdAt, order: DESC }) {
            nodes { createdAt }
          }
        }
        """
        data = linear_query(query, {"id": project_id})
        if "errors" in data:
            continue

        project = (data.get("data") or {}).get("project") or {}
        issues = project.get("issues", {}).get("nodes", []) or []
        updates = (data.get("data", {}).get("projectUpdates", {}).get("nodes", []) or [])

        # How many issues are "started" (in-progress)?
        started_issues = [i for i in issues if i.get("state", {}).get("type") == "started"]
        # When was the last update?
        last_update = updates[0].get("createdAt", "") if updates else ""
        last_update_days = 999
        if last_update:
            last_update_days = (datetime.now(timezone.utc) - datetime.fromisoformat(last_update.replace("Z", "+00:00"))).days

        # Criteria for stalled: many in-progress AND no recent update
        if len(started_issues) >= 3 and last_update_days >= days_threshold:
            # Count how many of the started issues haven't moved in 5+ days
            still_stalled = [
                i for i in started_issues
                if (i.get("updatedAt", "")[:10]) < cutoff
            ]
            if still_stalled:
                stalled.append({
                    "name": project_name,
                    "started_count": len(started_issues),
                    "stalled_count": len(still_stalled),
                    "days_since_update": last_update_days,
                    "issues": still_stalled[:3],  # top 3 stale
                })

    stalled.sort(key=lambda x: -x["days_since_update"])
    return stalled


# ── Signal 3: Overloaded members (5+ open issues, low velocity) ──────────────
def fetch_overloaded_members() -> list:
    """Members with 5+ open issues and no completed issues in 14 days."""
    env = load_env()
    key = env.get("LINEAR_API_KEY", "")
    if not key:
        return []

    # Get all users
    data = linear_query("query { users(first: 20) { nodes { id name email } } }")
    if "errors" in data:
        return []

    users = (data.get("data") or {}).get("users", {}).get("nodes", [])
    cutoff_14d = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")

    overloaded = []
    for user in users:
        uid = user.get("id", "")
        uname = user.get("name", "")

        # Skip ex-members
        if any(ex in uname.lower() for ex in EX_MEMBERS):
            continue

        # Get open issues + issues completed in last 14 days
        gql = """
        query($uid: String!, $cutoff: DateTime!) {
          open: issues(
            filter: { assignee: { id: { eq: $uid } }, state: { type: { nin: ["completed","canceled"] } } }
            first: 50
          ) { totalCount }
          completed_recently: issues(
            filter: { assignee: { id: { eq: $uid } }, state: { type: { eq: "completed" } }, updatedAt: { gte: $cutoff } }
            first: 10
          ) { totalCount }
        }
        """
        result = linear_query(gql, {"uid": uid, "cutoff": cutoff_14d})
        if "errors" in result:
            continue

        open_count = (result.get("data", {}).get("open") or {}).get("totalCount", 0)
        completed_14d = (result.get("data", {}).get("completed_recently") or {}).get("totalCount", 0)

        # Overloaded: 5+ open AND <2 completed in 14 days
        if open_count >= 5 and completed_14d < 2:
            overloaded.append({
                "name": uname,
                "open_issues": open_count,
                "completed_14d": completed_14d,
                "ratio": round(open_count / max(completed_14d, 1), 1),
            })

    overloaded.sort(key=lambda x: -x["open_issues"])
    return overloaded


# ── Signal 4: Overdue issues (past due date) ──────────────────────────────────
def fetch_overdue_issues() -> list:
    """Issues with a due date in the past."""
    overdue = []
    today = datetime.now().strftime("%Y-%m-%d")

    for project_name, project_id in LINEAR_PROJECT_IDS.items():
        query = """
        query($id: String!) {
          project(id: $id) {
            name
            issues(filter: { dueDate: { lte: "%s" } }, first: 50) {
              nodes {
                title identifier dueDate priority
                state { name type }
                assignee { name }
              }
            }
          }
        }
        """ % today

        data = linear_query(query, {"id": project_id})
        if "errors" in data:
            continue

        issues = (data.get("data", {}).get("project") or {}).get("issues", {}).get("nodes", []) or []
        for issue in issues:
            if issue.get("state", {}).get("type") not in ("completed", "canceled"):
                due = issue.get("dueDate", "")[:10]
                days_over = (datetime.now() - datetime.strptime(due, "%Y-%m-%d")).days if due else 0
                overdue.append({
                    "title": issue.get("title", "?")[:60],
                    "id": issue.get("identifier", ""),
                    "due": due,
                    "days_over": days_over,
                    "project": project_name,
                    "assignee": issue.get("assignee", {}).get("name", "unassigned"),
                    "priority": issue.get("priority", 0),
                })

    overdue.sort(key=lambda x: -x["days_over"])
    return overdue


# ── Signal 5: Old PRs without reviewers ─────────────────────────────────────
def fetch_orphaned_prs(days_threshold: int = 7) -> list:
    """PRs open >7 days with no review requests assigned."""
    orphaned = []

    for org in GITHUB_ORGS:
        try:
            raw = subprocess.check_output(
                f'gh api orgs/{org}/repos --paginate --jq ".[].nameWithOwner"',
                shell=True, stderr=subprocess.DEVNULL, timeout=20
            )
            repos = [r.strip() for r in raw.decode().strip().splitlines() if r.strip()]
        except Exception:
            continue

        for repo in repos:
            try:
                raw = subprocess.check_output(
                    f'gh api repos/{repo}/pulls?state=open&per_page=50 --paginate',
                    shell=True, stderr=subprocess.DEVNULL, timeout=20
                )
                for pr in json.loads(raw):
                    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    age_days = (datetime.now(timezone.utc) - created).days
                    reviewers = pr.get("requested_reviewers", []) or []
                    if age_days >= days_threshold and not reviewers:
                        orphaned.append({
                            "repo": repo,
                            "number": pr["number"],
                            "title": pr["title"][:65],
                            "author": pr["user"]["login"],
                            "age_days": age_days,
                        })
            except Exception:
                pass

    orphaned.sort(key=lambda x: -x["age_days"])
    return orphaned


# ── Build summary ────────────────────────────────────────────────────────────
def build_radar(quiet_repos, stalled_projects, overloaded, overdue, orphaned) -> str:
    lines = []
    today = datetime.now().strftime("%-d %b %Y")
    lines.append(f"🔭 *Risk Radar* · {today}\n")

    has_risks = quiet_repos or stalled_projects or overloaded or overdue or orphaned

    if not has_risks:
        lines.append("✅ All clear — no risks detected.")
        return "\n".join(lines)

    if quiet_repos:
        lines.append(f"🔇 *Quiet repos* ({len(quiet_repos)} — no commits in 10+ days)")
        for r in quiet_repos[:5]:
            d = r["days"]
            tag = "🔴" if d > 30 else "🟡"
            lines.append(f"  {tag} `{r['repo'].split('/')[-1]}` — last: {r['last_commit']} ({d}d)")
        if len(quiet_repos) > 5:
            lines.append(f"  _+{len(quiet_repos)-5} more_")
        lines.append("")

    if stalled_projects:
        lines.append(f"⏸️ *Stalled projects* ({len(stalled_projects)} — started but no update)")
        for p in stalled_projects[:4]:
            lines.append(f"  🔴 *{p['name']}* — {p['started_count']} in-progress, "
                         f"{p['stalled_count']} stale · {p['days_since_update']}d silent")
            for i in p["issues"][:2]:
                lines.append(f"     └ `{(i.get('identifier') or '')}` {i.get('title', '')[:50]}")
        lines.append("")

    if overdue:
        lines.append(f"⏰ *Overdue issues* ({len(overdue)} past due date)")
        for o in overdue[:5]:
            days = o["days_over"]
            tag = "🔴" if days >= 3 else "🟡"
            assignee = f"@{o['assignee']}" if o["assignee"] != "unassigned" else "⊘ unassigned"
            lines.append(f"  {tag} `{o['id']}` {o['title']} — *{days}d overdue* [{assignee}]")
        if len(overdue) > 5:
            lines.append(f"  _+{len(overdue)-5} more_")
        lines.append("")

    if overloaded:
        lines.append(f"⚖️ *Overloaded members* (5+ open, <2 closed in 14d)")
        for m in overloaded[:4]:
            lines.append(f"  🔴 *{m['name']}* — {m['open_issues']} open · {m['completed_14d']} completed (14d)")
        lines.append("")

    if orphaned:
        lines.append(f"🤷 *Orphaned PRs* ({len(orphaned)} open >7d, no reviewers)")
        for p in orphaned[:4]:
            lines.append(f"  🟡 `{p['repo'].split('/')[-1]}#{p['number']}` {p['title']} — "
                         f"by {p['author']} · {p['age_days']}d")
        lines.append("")

    lines.append("_Axeng risk-radar.py_")
    return "\n".join(lines)


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


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="Print only")
    args = parser.parse_args()

    print("🔭 Risk Radar — scanning...")

    print("  Checking quiet repos...")
    quiet = fetch_quiet_repos()

    print("  Checking stalled projects...")
    stalled = fetch_stalled_projects()

    print("  Checking overloaded members...")
    overloaded = fetch_overloaded_members()

    print("  Checking overdue issues...")
    overdue = fetch_overdue_issues()

    print("  Checking orphaned PRs...")
    orphaned = fetch_orphaned_prs()

    total = len(quiet) + len(stalled) + len(overloaded) + len(overdue) + len(orphaned)
    print(f"\n  Found {total} risk signals across {len(quiet)} repos, "
          f"{len(stalled)} stalled projects, {len(overloaded)} overloaded members, "
          f"{len(overdue)} overdue, {len(orphaned)} orphaned PRs")

    report = build_radar(quiet, stalled, overloaded, overdue, orphaned)
    print("\n" + report)

    if not args.dry:
        send_telegram(report)

    print("\n✅ Done.")