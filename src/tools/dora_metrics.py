#!/usr/bin/env python3
"""
DORA Metrics Analysis
Calculates the 4 key DORA metrics using Linear + GitHub data.

DORA Metrics:
1. Deployment Frequency - How often we ship (GitHub PR merges)
2. Lead Time for Changes - Code commit → production (PR creation → merge)
3. Mean Time to Recovery (MTTR) - Time to fix incidents (Linear issue lifecycle)
4. Change Failure Rate - % of deployments causing issues (GitHub reverts + Linear bugs)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get, github_repos
from tools.linear_tool import linear_query
from tools.github_activity import gh_api


def calculate_deployment_frequency(days: int = 30) -> dict:
    """
    Calculate deployment frequency using GitHub PR merges as proxy.

    Assumption: Merged PRs to main/master = deployments
    """
    repos = github_repos()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    total_merges = 0
    merges_by_repo = {}

    for repo in repos:
        try:
            # Get merged PRs
            query = f"repo:{repo} is:pr is:merged merged:>={since}"
            result = gh_api(f"search/issues?q={query}&per_page=100")

            if isinstance(result, dict) and "items" in result:
                count = len(result["items"])
                total_merges += count
                merges_by_repo[repo] = count
        except:
            pass

    # Calculate frequency
    deploys_per_day = total_merges / days if days > 0 else 0
    deploys_per_week = deploys_per_day * 7

    # DORA tier
    if deploys_per_day >= 1:
        tier = "Elite"
        emoji = "🟢"
    elif deploys_per_day >= 0.14:  # ~1 per week
        tier = "High"
        emoji = "🟡"
    elif deploys_per_day >= 0.03:  # ~1 per month
        tier = "Medium"
        emoji = "🟠"
    else:
        tier = "Low"
        emoji = "🔴"

    return {
        "metric": "Deployment Frequency",
        "total_deployments": total_merges,
        "period_days": days,
        "per_day": round(deploys_per_day, 2),
        "per_week": round(deploys_per_week, 1),
        "dora_tier": tier,
        "emoji": emoji,
        "by_repo": merges_by_repo
    }


def calculate_lead_time(days: int = 30) -> dict:
    """
    Calculate lead time for changes using PR lifecycle.

    Lead time = First commit to PR merge
    """
    repos = github_repos()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    lead_times = []
    repo_lead_times = {}

    for repo in repos:
        try:
            # Get merged PRs with details
            query = f"repo:{repo} is:pr is:merged merged:>={since}"
            result = gh_api(f"search/issues?q={query}&per_page=50")

            if isinstance(result, dict) and "items" in result:
                for pr in result["items"]:
                    pr_number = pr.get("number")

                    # Get PR details for created/merged dates
                    pr_detail = gh_api(f"repos/{repo}/pulls/{pr_number}")

                    if isinstance(pr_detail, dict):
                        created_at = pr_detail.get("created_at")
                        merged_at = pr_detail.get("merged_at")

                        if created_at and merged_at:
                            try:
                                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                                merged = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))

                                lead_time_hours = (merged - created).total_seconds() / 3600
                                lead_times.append(lead_time_hours)

                                if repo not in repo_lead_times:
                                    repo_lead_times[repo] = []
                                repo_lead_times[repo].append(lead_time_hours)
                            except:
                                pass
        except:
            pass

    if not lead_times:
        return {
            "metric": "Lead Time for Changes",
            "error": "No merged PRs found in period"
        }

    # Calculate statistics
    avg_lead_time_hours = sum(lead_times) / len(lead_times)
    avg_lead_time_days = avg_lead_time_hours / 24
    median_lead_time = sorted(lead_times)[len(lead_times) // 2]

    # DORA tier
    if avg_lead_time_days < 1:
        tier = "Elite"
        emoji = "🟢"
    elif avg_lead_time_days < 7:
        tier = "High"
        emoji = "🟡"
    elif avg_lead_time_days < 30:
        tier = "Medium"
        emoji = "🟠"
    else:
        tier = "Low"
        emoji = "🔴"

    # Calculate per-repo averages
    repo_averages = {}
    for repo, times in repo_lead_times.items():
        repo_averages[repo] = round(sum(times) / len(times) / 24, 1) if times else 0

    return {
        "metric": "Lead Time for Changes",
        "sample_size": len(lead_times),
        "average_hours": round(avg_lead_time_hours, 1),
        "average_days": round(avg_lead_time_days, 1),
        "median_hours": round(median_lead_time, 1),
        "dora_tier": tier,
        "emoji": emoji,
        "by_repo_days": repo_averages
    }


def calculate_mttr(days: int = 90) -> dict:
    """
    Calculate Mean Time to Recovery using Linear bug lifecycle.

    MTTR = Time from bug creation to resolution
    Filters for issues labeled as bugs/incidents
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    query = f"""
    query {{
      issues(
        filter: {{
          priority: {{ in: [1, 2] }}
          state: {{ type: {{ eq: "completed" }} }}
          completedAt: {{ gte: "{since}" }}
        }}
        first: 100
      ) {{
        nodes {{
          identifier title
          priority
          createdAt completedAt
          labels {{ nodes {{ name }} }}
        }}
      }}
    }}
    """

    result = linear_query(query)
    issues = result.get("data", {}).get("issues", {}).get("nodes", [])

    # Filter for bugs/incidents (priority 1-2 or labeled as bug)
    incidents = []
    for issue in issues:
        labels = [l.get("name", "").lower() for l in issue.get("labels", {}).get("nodes", [])]
        is_incident = (
            issue.get("priority") in [1, 2] or
            any(label in labels for label in ["bug", "incident", "hotfix", "critical"])
        )

        if is_incident:
            incidents.append(issue)

    if not incidents:
        return {
            "metric": "Mean Time to Recovery (MTTR)",
            "error": "No incidents found in period",
            "hint": "Try longer period or check Linear priorities"
        }

    # Calculate recovery times
    recovery_times = []
    for incident in incidents:
        try:
            created = datetime.fromisoformat(incident.get("createdAt", "").replace("Z", "+00:00"))
            completed = datetime.fromisoformat(incident.get("completedAt", "").replace("Z", "+00:00"))

            recovery_hours = (completed - created).total_seconds() / 3600
            recovery_times.append(recovery_hours)
        except:
            pass

    if not recovery_times:
        return {
            "metric": "Mean Time to Recovery (MTTR)",
            "error": "Could not calculate recovery times"
        }

    avg_mttr_hours = sum(recovery_times) / len(recovery_times)
    avg_mttr_days = avg_mttr_hours / 24

    # DORA tier
    if avg_mttr_hours < 1:
        tier = "Elite"
        emoji = "🟢"
    elif avg_mttr_hours < 24:
        tier = "High"
        emoji = "🟡"
    elif avg_mttr_hours < 168:  # 1 week
        tier = "Medium"
        emoji = "🟠"
    else:
        tier = "Low"
        emoji = "🔴"

    return {
        "metric": "Mean Time to Recovery (MTTR)",
        "sample_size": len(recovery_times),
        "average_hours": round(avg_mttr_hours, 1),
        "average_days": round(avg_mttr_days, 2),
        "dora_tier": tier,
        "emoji": emoji,
        "incidents_analyzed": len(incidents)
    }


def calculate_change_failure_rate(days: int = 30) -> dict:
    """
    Calculate change failure rate using GitHub reverts + Linear bugs.

    Failure rate = (Reverts + Post-deploy bugs) / Total deployments
    """
    repos = github_repos()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    total_merges = 0
    total_reverts = 0
    revert_prs = []

    for repo in repos:
        try:
            # Count all merges
            merge_query = f"repo:{repo} is:pr is:merged merged:>={since}"
            merge_result = gh_api(f"search/issues?q={merge_query}&per_page=100")

            if isinstance(merge_result, dict) and "items" in merge_result:
                total_merges += len(merge_result["items"])

            # Count reverts
            revert_query = f"repo:{repo} is:pr is:merged merged:>={since} revert in:title"
            revert_result = gh_api(f"search/issues?q={revert_query}&per_page=100")

            if isinstance(revert_result, dict) and "items" in revert_result:
                reverts = revert_result["items"]
                total_reverts += len(reverts)
                revert_prs.extend([{"repo": repo, "title": pr.get("title")} for pr in reverts])
        except:
            pass

    # Get post-deploy bugs from Linear (bugs created after deployments)
    bug_query = f"""
    query {{
      issues(
        filter: {{
          createdAt: {{ gte: "{since}" }}
          labels: {{ some: {{ name: {{ in: ["bug", "incident", "hotfix"] }} }} }}
        }}
        first: 50
      ) {{
        nodes {{
          identifier title createdAt
        }}
      }}
    }}
    """

    linear_result = linear_query(bug_query)
    bugs = linear_result.get("data", {}).get("issues", {}).get("nodes", [])
    post_deploy_bugs = len(bugs)

    # Calculate failure rate
    total_failures = total_reverts + post_deploy_bugs
    failure_rate = (total_failures / total_merges * 100) if total_merges > 0 else 0

    # DORA tier
    if failure_rate < 15:
        tier = "Elite"
        emoji = "🟢"
    elif failure_rate < 30:
        tier = "High"
        emoji = "🟡"
    elif failure_rate < 45:
        tier = "Medium"
        emoji = "🟠"
    else:
        tier = "Low"
        emoji = "🔴"

    return {
        "metric": "Change Failure Rate",
        "total_deployments": total_merges,
        "total_failures": total_failures,
        "reverts": total_reverts,
        "post_deploy_bugs": post_deploy_bugs,
        "failure_rate_pct": round(failure_rate, 1),
        "dora_tier": tier,
        "emoji": emoji,
        "recent_reverts": revert_prs[:5]
    }


def dora_metrics(days: int = 30) -> dict:
    """Get all DORA metrics in one report."""
    deployment_freq = calculate_deployment_frequency(days)
    lead_time = calculate_lead_time(days)
    mttr = calculate_mttr(90)  # Longer period for MTTR
    change_failure = calculate_change_failure_rate(days)

    # Calculate overall DORA tier
    tiers = [
        deployment_freq.get("dora_tier"),
        lead_time.get("dora_tier"),
        mttr.get("dora_tier"),
        change_failure.get("dora_tier")
    ]

    tier_scores = {"Elite": 4, "High": 3, "Medium": 2, "Low": 1}
    avg_score = sum(tier_scores.get(t, 1) for t in tiers if t) / len([t for t in tiers if t])

    if avg_score >= 3.5:
        overall_tier = "Elite"
    elif avg_score >= 2.5:
        overall_tier = "High"
    elif avg_score >= 1.5:
        overall_tier = "Medium"
    else:
        overall_tier = "Low"

    return {
        "tool": "dora_metrics",
        "timestamp": datetime.now().isoformat(),
        "period_days": days,
        "overall_tier": overall_tier,
        "metrics": {
            "deployment_frequency": deployment_freq,
            "lead_time": lead_time,
            "mttr": mttr,
            "change_failure_rate": change_failure
        },
        "summary": _generate_dora_summary(deployment_freq, lead_time, mttr, change_failure, overall_tier)
    }


def _generate_dora_summary(deploy, lead, mttr, failure, overall) -> dict:
    """Generate summary insights from DORA metrics."""
    strengths = []
    weaknesses = []

    # Check each metric
    if deploy.get("dora_tier") in ["Elite", "High"]:
        strengths.append("High deployment frequency")
    else:
        weaknesses.append("Low deployment frequency - consider smaller, more frequent releases")

    if lead.get("dora_tier") in ["Elite", "High"]:
        strengths.append("Fast lead time")
    else:
        weaknesses.append(f"Slow lead time ({lead.get('average_days', 0)}d) - streamline PR review process")

    if mttr.get("dora_tier") in ["Elite", "High"]:
        strengths.append("Quick incident recovery")
    elif not mttr.get("error"):
        weaknesses.append(f"Slow recovery ({mttr.get('average_hours', 0)}h) - improve monitoring and response")

    if failure.get("dora_tier") in ["Elite", "High"]:
        strengths.append("Low change failure rate")
    else:
        weaknesses.append(f"High failure rate ({failure.get('failure_rate_pct', 0)}%) - strengthen testing and staging")

    return {
        "overall_tier": overall,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "top_priority": weaknesses[0] if weaknesses else "Maintain current performance"
    }


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    result = dora_metrics(days)
    print(json.dumps(result, indent=2, default=str))
