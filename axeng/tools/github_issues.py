#!/usr/bin/env python3
"""
GitHub Issues Tool — Operational risk signals for CEO steering report.
Uses a single GraphQL batch query per org (not per-repo REST) to avoid
N+1 API calls and rate-limit exhaustion.

Main entry:  fetch_issue_signals(repos: list[str]) -> dict[str, IssueSignals]
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from project_map import build_maps
from tools.steering_schema import IssueSignals, Evidence

# Keywords that indicate a thread is blocked on an external dependency
BLOCKER_KEYWORDS = (
    "blocked by", "blocking", "waiting on", "depends on",
    "dependency on", "waiting for", "can't proceed", "cannot proceed",
)

STALE_DAYS = 10   # open issue not updated in N days = stale


# ── GitHub GraphQL via gh CLI ────────────────────────────────────────────────

def _gh_graphql(query: str, variables: dict | None = None) -> dict:
    """Execute a GitHub GraphQL query via the gh CLI."""
    payload: dict = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        result = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=45,
        )
        if result.returncode != 0:
            stderr = result.stderr.lower()
            if "authentication" in stderr or "not authenticated" in stderr:
                return {"error": "GitHub authentication failed — run 'gh auth login'"}
            return {"error": result.stderr.strip() or "GraphQL call failed"}
        return json.loads(result.stdout)
    except FileNotFoundError:
        return {"error": "GitHub CLI (gh) not installed — brew install gh"}
    except Exception as e:
        return {"error": str(e)}


def _gh_rest_issues(repo: str, state: str = "open", per_page: int = 100) -> list[dict]:
    """Fallback: fetch issues for a single repo via REST."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/issues",
             "--paginate", "-f", f"state={state}", "-f", f"per_page={per_page}"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            # gh --paginate may return a list or wrapped object
            if isinstance(data, list):
                return data
            return data.get("items", [])
    except Exception:
        pass
    return []


# ── Fetch issues: GraphQL batch by org ──────────────────────────────────────

_REPO_ISSUES_FRAGMENT = """
fragment repoIssues on Repository {
  nameWithOwner
  open: issues(states: OPEN, first: 100, orderBy: {field: UPDATED_AT, direction: ASC}) {
    nodes {
      number
      title
      createdAt
      updatedAt
      assignees(first: 1) { nodes { login } }
      milestone { dueOn }
      labels(first: 5) { nodes { name } }
      body
      comments(last: 3) { nodes { body } }
    }
  }
  closed: issues(states: CLOSED, first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
    nodes {
      number
      closedAt
    }
  }
}
"""


def _fetch_org_issues(org: str, repo_names: list[str]) -> dict[str, list[dict]]:
    """
    Batch-fetch open + recently closed issues for up to 20 repos in one GraphQL query.
    Returns {full_repo_name: {"open": [...], "closed": [...]}}
    """
    if not repo_names:
        return {}

    # Build one aliased field per repo
    aliases = []
    for i, name in enumerate(repo_names[:20]):  # GraphQL complexity cap
        safe = f"r{i}"
        aliases.append(f'{safe}: repository(owner: "{org}", name: "{name}") {{ ...repoIssues }}')

    query = f"""
    {_REPO_ISSUES_FRAGMENT}
    query {{
      {chr(10).join(aliases)}
    }}
    """

    result = _gh_graphql(query)
    if "error" in result:
        return {}

    data = result.get("data", {})
    out: dict[str, dict] = {}
    for i, name in enumerate(repo_names[:20]):
        alias = f"r{i}"
        repo_data = data.get(alias) or {}
        full_name = f"{org}/{name}"
        out[full_name] = {
            "open": (repo_data.get("open") or {}).get("nodes") or [],
            "closed": (repo_data.get("closed") or {}).get("nodes") or [],
        }

    return out


def fetch_raw_issues(repos: list[str]) -> dict[str, dict]:
    """
    Fetch open + recently closed issues for all repos, grouped by full repo name.
    Returns {repo: {"open": [...], "closed": [...]}}
    Groups by org, batch-queries per org, falls back to REST per repo on failure.
    """
    by_org: dict[str, list[str]] = {}
    for repo in repos:
        if "/" not in repo:
            continue
        org, name = repo.split("/", 1)
        by_org.setdefault(org, []).append(name)

    all_issues: dict[str, dict] = {}

    for org, names in by_org.items():
        batch = _fetch_org_issues(org, names)
        if batch:
            all_issues.update(batch)
        else:
            # GraphQL failed — fall back to REST per repo (open issues only)
            for name in names:
                full = f"{org}/{name}"
                all_issues[full] = {
                    "open": _gh_rest_issues(full, state="open"),
                    "closed": _gh_rest_issues(full, state="closed", per_page=30),
                }

    return all_issues


# ── Signal detection ─────────────────────────────────────────────────────────

def _is_stale(issue: dict, cutoff: datetime) -> bool:
    updated = issue.get("updatedAt") or issue.get("updated_at", "")
    if not updated:
        return True
    try:
        dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        return dt < cutoff
    except ValueError:
        return False


def _is_unowned(issue: dict) -> bool:
    # GraphQL shape
    assignees = issue.get("assignees", {})
    if isinstance(assignees, dict):
        return len(assignees.get("nodes", [])) == 0
    # REST shape
    if isinstance(assignees, list):
        return len(assignees) == 0
    return True


def _is_overdue(issue: dict, target_date_str: str | None) -> bool:
    today = datetime.now(timezone.utc).date()

    # Check milestone due date
    milestone = issue.get("milestone")
    if milestone:
        due = milestone.get("dueOn") or milestone.get("due_on")
        if due:
            try:
                return datetime.fromisoformat(due[:10]).date() < today
            except ValueError:
                pass

    # Check against project target date
    if target_date_str:
        try:
            target = datetime.fromisoformat(target_date_str[:10]).date()
            created = issue.get("createdAt") or issue.get("created_at", "")
            if created:
                created_date = datetime.fromisoformat(created.replace("Z", "+00:00")).date()
                # Issue predates target and is still open past it
                if created_date < target < today:
                    return True
        except ValueError:
            pass

    return False


def _is_blocked(issue: dict) -> bool:
    text = (issue.get("body") or "").lower()
    comments = issue.get("comments", {})
    comment_bodies = ""
    if isinstance(comments, dict):
        comment_bodies = " ".join(
            (c.get("body") or "") for c in comments.get("nodes", [])
        ).lower()
    elif isinstance(comments, list):
        comment_bodies = " ".join((c.get("body") or "") for c in comments).lower()

    combined = text + " " + comment_bodies
    return any(kw in combined for kw in BLOCKER_KEYWORDS)


def _issue_label(issue: dict, repo: str) -> str:
    num = issue.get("number", "?")
    title = (issue.get("title") or "")[:60]
    return f"{repo}#{num} — {title}"


# ── Compute IssueSignals per project ────────────────────────────────────────

def compute_issue_signals(
    project_repos: list[str],
    raw_issues: dict[str, dict],
    week_start: str,
    target_date: str | None = None,
) -> tuple[IssueSignals, list[Evidence]]:
    """
    Aggregate raw issues for a project's repos into an IssueSignals object.
    raw_issues shape: {repo: {"open": [...], "closed": [...]}}
    Also returns a list of Evidence items for traceability.
    """
    from tools.steering_schema import Evidence

    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)
    week_start_dt = datetime.fromisoformat(week_start + "T00:00:00+00:00")

    stale: list[str] = []
    unowned: list[str] = []
    overdue: list[str] = []
    blocked: list[str] = []
    opened_labels: list[str] = []
    closed_labels: list[str] = []
    created_this_week = 0
    closed_this_week = 0

    for repo in project_repos:
        repo_data = raw_issues.get(repo, {})
        # Support both new dict shape and legacy flat list (REST fallback)
        if isinstance(repo_data, list):
            open_issues, closed_issues = repo_data, []
        else:
            open_issues = repo_data.get("open", [])
            closed_issues = repo_data.get("closed", [])

        for issue in open_issues:
            label = _issue_label(issue, repo)

            if _is_stale(issue, stale_cutoff):
                stale.append(label)
            if _is_unowned(issue):
                unowned.append(label)
            if _is_overdue(issue, target_date):
                overdue.append(label)
            if _is_blocked(issue):
                blocked.append(label)

            created = issue.get("createdAt") or issue.get("created_at", "")
            if created:
                try:
                    if datetime.fromisoformat(created.replace("Z", "+00:00")) >= week_start_dt:
                        created_this_week += 1
                        opened_labels.append(label)
                except ValueError:
                    pass

        # Count issues actually closed this week
        for issue in closed_issues:
            closed_at = issue.get("closedAt") or issue.get("closed_at", "")
            if closed_at:
                try:
                    if datetime.fromisoformat(closed_at.replace("Z", "+00:00")) >= week_start_dt:
                        closed_this_week += 1
                        closed_labels.append(_issue_label(issue, repo))
                except ValueError:
                    pass

    backlog_growth = created_this_week - closed_this_week  # can be negative = backlog shrinking

    # Risk score: weighted sum, 0–100. Only penalise positive backlog growth.
    risk_score = min(
        100,
        len(stale) * 3 +
        len(unowned) * 4 +
        len(overdue) * 8 +
        len(blocked) * 10 +
        max(0, backlog_growth) * 2,
    )

    signals = IssueSignals(
        stale_count=len(stale),
        unowned_count=len(unowned),
        overdue_count=len(overdue),
        backlog_growth=backlog_growth,
        blocked_threads=len(blocked),
        opened_this_week=created_this_week,
        closed_this_week=closed_this_week,
        top_stale=stale[:3],
        top_blocked=blocked[:3],
        recently_opened=opened_labels[:5],
        recently_closed=closed_labels[:5],
        risk_score=round(risk_score, 1),
    )

    evidence: list[Evidence] = []
    for label in blocked[:3]:
        evidence.append(Evidence(source="github_issues", text=f"Blocked thread: {label}", severity="critical"))
    for label in overdue[:3]:
        evidence.append(Evidence(source="github_issues", text=f"Overdue: {label}", severity="warning"))
    for label in stale[:3]:
        evidence.append(Evidence(source="github_issues", text=f"Stale: {label}", severity="info"))

    return signals, evidence


# ── Public entry point ───────────────────────────────────────────────────────

def enrich_with_issue_signals(
    project_cards: list,
    week_start: str,
) -> list:
    """
    Fetch GitHub Issues for all project repos and attach IssueSignals
    to each ProjectCard in place. Returns the same list (mutated).
    """
    # Collect all repos across all projects
    all_repos: list[str] = []
    for card in project_cards:
        all_repos.extend(card.repos)

    if not all_repos:
        return project_cards

    print("  🐙 Fetching GitHub Issues...", file=sys.stderr)
    raw = fetch_raw_issues(list(set(all_repos)))

    if not raw:
        print("  ⚠️  No GitHub Issues data — skipping issue signals", file=sys.stderr)
        return project_cards

    for card in project_cards:
        if not card.repos:
            continue
        signals, evidence = compute_issue_signals(
            card.repos, raw, week_start, card.target_date
        )
        card.issue_signals = signals
        card.evidence.extend(evidence)

        # Enrich true blockers list only with explicit blocked threads.
        if signals.top_blocked:
            card.blockers.extend(signals.top_blocked[:2])
        if signals.overdue_count > 0:
            card.health_signals.append(
                f"{signals.overdue_count} overdue issue{'s' if signals.overdue_count > 1 else ''}"
            )

    return project_cards


# ── CLI entry ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch GitHub issue signals")
    parser.add_argument("repos", nargs="+", help="Repos in org/name format")
    parser.add_argument("--week-start", default=str(
        (datetime.now() - timedelta(days=7)).date()
    ))
    args = parser.parse_args()

    raw = fetch_raw_issues(args.repos)
    signals, evidence = compute_issue_signals(args.repos, raw, args.week_start)

    print(json.dumps({
        "stale": signals.stale_count,
        "unowned": signals.unowned_count,
        "overdue": signals.overdue_count,
        "backlog_growth": signals.backlog_growth,
        "blocked_threads": signals.blocked_threads,
        "risk_score": signals.risk_score,
        "top_stale": signals.top_stale,
        "top_blocked": signals.top_blocked,
        "evidence": [{"source": e.source, "text": e.text, "severity": e.severity} for e in evidence],
    }, indent=2))
