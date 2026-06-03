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
        if result.returncode != 0:
            if "authentication" in result.stderr.lower() or "not authenticated" in result.stderr.lower():
                return {
                    "error": "GitHub authentication failed",
                    "hint": "Run 'gh auth login' or set GITHUB_TOKEN in 'axeng configure'",
                    "setup_url": "https://github.com/settings/tokens"
                }
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except FileNotFoundError:
        return {
            "error": "GitHub CLI (gh) not installed",
            "hint": "Install with: brew install gh",
            "setup_url": "https://cli.github.com"
        }
    except Exception as e:
        return {"error": str(e)}
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

    # Fetch merged PRs and reviews — only meaningful for a specific person.
    # Team-wide PR titles are fetched per active repo by commits_summary_from_activity.
    if github_user:
        pr_query = f"author:{github_user} is:pr merged:>={since}"
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
    since_dt = datetime.strptime(since, "%Y-%m-%d")
    repos = github_repos()
    by_repo = {}
    
    for repo in repos:
        try:
            commits = gh_api(f"repos/{repo}/commits?since={since}&per_page=100")
            pulls = gh_api(f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30")
            recent_pr_titles = []
            if isinstance(pulls, list):
                for pr in pulls:
                    merged_at = pr.get("merged_at")
                    if not merged_at:
                        continue
                    try:
                        merged_dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    except ValueError:
                        continue
                    if merged_dt >= since_dt:
                        title = (pr.get("title") or "").strip()
                        if title:
                            recent_pr_titles.append(title)
            if isinstance(commits, list):
                by_repo[repo] = {
                    "count": len(commits),
                    "recent": [c.get("sha", "")[:7] for c in commits[:5]],
                    "recent_messages": [
                        (c.get("commit", {}) or {}).get("message", "").split("\n")[0].strip()
                        for c in commits[:30]
                        if ((c.get("commit", {}) or {}).get("message", "").split("\n")[0].strip())
                    ],
                    "recent_pr_titles": recent_pr_titles[:10],
                }
        except Exception:
            pass

    return {
        "tool": "github_commits_summary",
        "days": days,
        "by_repo": by_repo
    }


def commits_summary_from_activity(activity: dict, days: int = 7) -> dict:
    """
    Derive a github_commits_summary-compatible by_repo dict from an already-fetched
    github_activity result. Avoids re-fetching commits for the same repos.
    Only fetches merged PR titles per repo (not covered by github_activity).
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    since_dt = datetime.strptime(since, "%Y-%m-%d")

    # Group flat commits by repo
    by_repo: dict[str, dict] = {}
    for c in activity.get("commits", []):
        repo = c.get("repo", "")
        if not repo:
            continue
        if repo not in by_repo:
            by_repo[repo] = {"count": 0, "recent_messages": [], "recent_pr_titles": []}
        by_repo[repo]["count"] += 1
        msg = c.get("message", "").strip()
        if msg and len(by_repo[repo]["recent_messages"]) < 30:
            by_repo[repo]["recent_messages"].append(msg)

    # Fetch merged PR titles per active repo (single extra call per repo)
    for repo in list(by_repo.keys()):
        try:
            pulls = gh_api(f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30")
            if isinstance(pulls, list):
                for pr in pulls:
                    merged_at = pr.get("merged_at")
                    if not merged_at:
                        continue
                    try:
                        merged_dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    except ValueError:
                        continue
                    if merged_dt >= since_dt:
                        title = (pr.get("title") or "").strip()
                        if title:
                            by_repo[repo]["recent_pr_titles"].append(title)
        except Exception:
            pass

    return {"tool": "github_commits_summary", "days": days, "by_repo": by_repo}


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


def github_pr_health(days: int = 14) -> dict:
    """
    Analyze PR health across repositories.

    Returns:
    - Open PRs with review status
    - Stale PRs (>3 days no activity)
    - Blocking reviews needed
    - Review velocity metrics
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    repos = github_repos()

    open_prs = []
    stale_prs = []
    needs_review = []
    approved_prs = []
    changes_requested = []

    now = datetime.now()
    stale_threshold = now - timedelta(days=3)

    for repo in repos:
        try:
            # Get open PRs
            prs = gh_api(f"repos/{repo}/pulls?state=open&per_page=50&sort=updated&direction=desc")

            if isinstance(prs, list):
                for pr in prs:
                    pr_data = {
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "repo": repo,
                        "url": pr.get("html_url"),
                        "author": pr.get("user", {}).get("login", "unknown"),
                        "created_at": pr.get("created_at"),
                        "updated_at": pr.get("updated_at"),
                        "draft": pr.get("draft", False),
                        "mergeable": pr.get("mergeable"),
                        "mergeable_state": pr.get("mergeable_state")
                    }

                    # Calculate age
                    try:
                        updated = datetime.fromisoformat(pr.get("updated_at", "").replace("Z", "+00:00"))
                        created = datetime.fromisoformat(pr.get("created_at", "").replace("Z", "+00:00"))
                        age_days = (now - updated.replace(tzinfo=None)).days
                        pr_data["age_days"] = age_days
                        pr_data["created_days_ago"] = (now - created.replace(tzinfo=None)).days
                    except:
                        pr_data["age_days"] = 0
                        pr_data["created_days_ago"] = 0

                    # Get review status
                    reviews = gh_api(f"repos/{repo}/pulls/{pr['number']}/reviews")
                    review_status = "pending"
                    reviewers_needed = []

                    if isinstance(reviews, list) and reviews:
                        # Get latest review from each reviewer
                        latest_reviews = {}
                        for review in reviews:
                            reviewer = review.get("user", {}).get("login")
                            if reviewer:
                                latest_reviews[reviewer] = review.get("state")

                        # Determine overall status
                        if "CHANGES_REQUESTED" in latest_reviews.values():
                            review_status = "changes_requested"
                        elif "APPROVED" in latest_reviews.values() and "CHANGES_REQUESTED" not in latest_reviews.values():
                            review_status = "approved"

                        pr_data["review_count"] = len(latest_reviews)
                        pr_data["reviewers"] = list(latest_reviews.keys())
                    else:
                        pr_data["review_count"] = 0
                        pr_data["reviewers"] = []

                    # Get requested reviewers
                    requested = pr.get("requested_reviewers", [])
                    if requested:
                        reviewers_needed = [r.get("login") for r in requested if r.get("login")]
                        pr_data["reviewers_needed"] = reviewers_needed

                    pr_data["review_status"] = review_status

                    open_prs.append(pr_data)

                    # Categorize
                    if not pr_data["draft"]:
                        if pr_data["age_days"] >= 3:
                            stale_prs.append(pr_data)

                        if review_status == "pending" and pr_data["review_count"] == 0:
                            needs_review.append(pr_data)
                        elif review_status == "approved":
                            approved_prs.append(pr_data)
                        elif review_status == "changes_requested":
                            changes_requested.append(pr_data)

        except Exception as e:
            # Skip repos that fail
            pass

    # Calculate metrics
    total_open = len([pr for pr in open_prs if not pr.get("draft")])
    avg_age = sum(pr.get("age_days", 0) for pr in open_prs) / len(open_prs) if open_prs else 0

    # Review velocity (PRs reviewed in last 7 days)
    recent_reviewed = []
    since_week = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    for repo in repos[:5]:  # Limit to avoid rate limits
        try:
            query = f"repo:{repo} is:pr reviewed:>={since_week}"
            result = gh_api(f"search/issues?q={query}&per_page=100")
            if isinstance(result, dict) and "items" in result:
                recent_reviewed.extend(result["items"])
        except:
            pass

    review_velocity = len(recent_reviewed) / 7 if recent_reviewed else 0  # PRs/day

    return {
        "tool": "github_pr_health",
        "timestamp": now.isoformat(),
        "metrics": {
            "total_open": total_open,
            "stale_count": len(stale_prs),
            "needs_review": len(needs_review),
            "approved": len(approved_prs),
            "changes_requested": len(changes_requested),
            "avg_age_days": round(avg_age, 1),
            "review_velocity_per_day": round(review_velocity, 1)
        },
        "open_prs": open_prs,
        "stale_prs": stale_prs[:10],  # Top 10 oldest
        "needs_review": needs_review[:10],
        "approved_prs": approved_prs[:5],
        "changes_requested": changes_requested[:5],
        "insights": _generate_pr_insights(open_prs, stale_prs, needs_review, approved_prs, review_velocity)
    }


def _generate_pr_insights(open_prs, stale_prs, needs_review, approved_prs, review_velocity) -> list:
    """Generate actionable insights from PR health data."""
    insights = []

    # Stale PR alert
    if len(stale_prs) > 5:
        insights.append({
            "level": "warning",
            "category": "stale_prs",
            "message": f"{len(stale_prs)} PRs are stale (>3 days no updates)",
            "action": "Review oldest PRs first or close if abandoned"
        })
    elif len(stale_prs) > 0:
        insights.append({
            "level": "info",
            "category": "stale_prs",
            "message": f"{len(stale_prs)} PRs waiting >3 days",
            "action": "Check if reviewers are assigned"
        })

    # Review bottleneck
    if len(needs_review) > 10:
        insights.append({
            "level": "critical",
            "category": "review_bottleneck",
            "message": f"{len(needs_review)} PRs have no reviews yet",
            "action": "Review capacity issue - consider distributing workload"
        })
    elif len(needs_review) > 5:
        insights.append({
            "level": "warning",
            "category": "review_bottleneck",
            "message": f"{len(needs_review)} PRs waiting for first review",
            "action": "Assign reviewers to unreviewed PRs"
        })

    # Approved PRs not merged
    if len(approved_prs) > 3:
        insights.append({
            "level": "warning",
            "category": "merge_delay",
            "message": f"{len(approved_prs)} approved PRs not yet merged",
            "action": "Check CI status and merge approved PRs"
        })

    # Low review velocity
    if review_velocity < 1.0 and len(open_prs) > 5:
        insights.append({
            "level": "info",
            "category": "low_velocity",
            "message": f"Review velocity is {review_velocity:.1f} PRs/day",
            "action": "Consider increasing review frequency"
        })

    # All good
    if not insights:
        insights.append({
            "level": "success",
            "category": "healthy",
            "message": "PR pipeline is healthy",
            "action": "Keep up the good work!"
        })

    return insights


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
    elif cmd == "pr-health":
        result = github_pr_health(days)
    else:
        result = {"error": f"Unknown command: {cmd}. Available: activity, commits, person, pr-health"}

    print(json.dumps(result, indent=2, default=str))
