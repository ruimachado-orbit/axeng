#!/usr/bin/env python3
"""
Team Intel — GitHub Activity Tool
Fetches commits and PRs via gh CLI.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get, github_repos, github_name_map


def gh_api(endpoint: str) -> dict:
    """Make GitHub API call via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return {}


def gh_cli(args: list) -> str:
    """Run gh CLI command, return output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def get_user_repos(person: str) -> list:
    """Get repos a user has contributed to."""
    repos = github_repos()
    result = []
    for repo in repos:
        try:
            # Check if user has contributed
            cmd = f"gh api repos/{repo}/contributors?per_page=20"
            contribs = gh_api(cmd.replace("https://api.github.com/", ""))
            if isinstance(contribs, list):
                for c in contribs:
                    if person.lower() in c.get("login", "").lower():
                        result.append(repo)
        except Exception:
            pass
    return result


# ─────────────────────────────────────────────
# TOOL: github_activity — Recent commits+PRs
# ─────────────────────────────────────────────

def github_activity(person: str = None, days: int = 7) -> dict:
    """
    Fetch GitHub commits and PRs for a person or team.
    
    person: GitHub username (uses config name_map if available)
    days: lookback window (default: 7)
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = {"commits": [], "pulls": [], "reviews": [], "summary": {}}
    
    # Resolve person via name map
    name_map = github_name_map()
    if person:
        github_user = name_map.get(person, {}).get("github", person)
    else:
        github_user = None

    repos = github_repos()
    if not repos:
        repos = ["org/repo"]  # fallback placeholder

    # Fetch commits
    for repo in repos:
        try:
            if github_user:
                commits = gh_api(f"repos/{repo}/commits?author={github_user}&since={since}&per_page=50")
            else:
                commits = gh_api(f"repos/{repo}/commits?since={since}&per_page=50")
            
            if isinstance(commits, list):
                for c in commits[:20]:
                    commit = c.get("commit", {})
                    result["commits"].append({
                        "sha": c.get("sha", "")[:7],
                        "message": commit.get("message", "").split("\n")[0],
                        "repo": repo,
                        "author": commit.get("author", {}).get("name", "unknown"),
                        "date": commit.get("author", {}).get("date", "")
                    })
        except Exception:
            pass

    # Fetch merged PRs
    if github_user:
        pr_query = f"author:{github_user} is:pr merged:>={since}"
    else:
        pr_query = f"is:pr merged:>={since}"
    
    prs = gh_api(f"search/issues?q={pr_query}&per_page=50&sort=updated")
    if isinstance(prs, dict) and "items" in prs:
        for pr in prs["items"][:20]:
            repo_name = pr.get("repository_url", "").split("/")[-1]
            result["pulls"].append({
                "number": pr.get("number"),
                "title": pr.get("title"),
                "repo": repo_name,
                "url": pr.get("html_url"),
                "merged_at": pr.get("closed_at"),
                "labels": [l["name"] for l in pr.get("labels", [])]
            })

    # Fetch reviews
    if github_user:
        review_query = f"reviewer:{github_user} is:pr updated:>={since}"
        reviews = gh_api(f"search/issues?q={review_query}&per_page=30")
        if isinstance(reviews, dict) and "items" in reviews:
            for pr in reviews["items"][:15]:
                repo_name = pr.get("repository_url", "").split("/")[-1]
                result["reviews"].append({
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "repo": repo_name,
                    "url": pr.get("html_url"),
                    "updated_at": pr.get("updated_at")
                })

    # Summary
    result["summary"] = {
        "person": person or "team",
        "days": days,
        "commits_count": len(result["commits"]),
        "prs_count": len(result["pulls"]),
        "reviews_count": len(result["reviews"])
    }

    return {
        "tool": "github_activity",
        "github_user": github_user,
        **result
    }


def github_commits_summary(days: int = 7) -> dict:
    """Get commit summary grouped by repo."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    repos = github_repos()
    by_repo = {}
    
    for repo in repos:
        try:
            commits = gh_api(f"repos/{repo}/commits?since={since}&per_page=100")
            if isinstance(commits, list):
                by_repo[repo] = {
                    "count": len(commits),
                    "recent": [c.get("sha", "")[:7] for c in commits[:5]]
                }
        except Exception:
            pass

    return {
        "tool": "github_commits_summary",
        "days": days,
        "by_repo": by_repo
    }


def github_person_summary(person: str, days: int = 7) -> dict:
    """Full GitHub summary for a person."""
    activity = github_activity(person, days)
    repos = get_user_repos(person)
    
    return {
        "tool": "github_person_summary",
        "person": person,
        "github_user": activity.get("github_user"),
        "repos_worked": repos,
        **activity
    }


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "activity"
    person = sys.argv[2] if len(sys.argv) > 2 else None
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 7

    if cmd == "activity":
        result = github_activity(person, days)
    elif cmd == "commits":
        result = github_commits_summary(days)
    elif cmd == "person":
        result = github_person_summary(person, days)
    else:
        result = {"error": f"Unknown command: {cmd}"}

    print(json.dumps(result, indent=2, default=str))