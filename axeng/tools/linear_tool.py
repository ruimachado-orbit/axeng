#!/usr/bin/env python3
"""
Team Intel — Linear Integration Tool
Fetches Linear issues and maps them to team members.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get, linear_workspace, vault_path


def load_env():
    """Load API key from .env file."""
    import os

    # Check AXENG_HOME first (for Homebrew installs)
    axeng_home = os.getenv("AXENG_HOME")
    if axeng_home:
        env_file = Path(axeng_home) / ".env"
    else:
        env_file = Path.home() / ".axeng" / ".env"

    env = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()

    # Also load from environment variables (overrides .env)
    for key in ["LINEAR_API_KEY", "GITHUB_TOKEN"]:
        if key in os.environ:
            env[key] = os.environ[key]

    return env


def linear_query(query: str, variables: dict = None) -> dict:
    """Execute GraphQL query against Linear API."""
    env = load_env()
    key = env.get("LINEAR_API_KEY", "")
    if not key:
        return {
            "errors": [{
                "message": "LINEAR_API_KEY not configured",
                "hint": "Run 'axeng configure' to set up Linear integration",
                "setup_url": "https://linear.app/settings/api"
            }]
        }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", "-X", "POST",
             "https://api.linear.app/graphql",
             "-H", f"Authorization: {key}",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload)],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)
    except Exception:
        return {"errors": [{"message": "Failed to connect to Linear API"}]}


# ─────────────────────────────────────────────
# TOOL: linear_issues — List open issues
# ─────────────────────────────────────────────

def linear_issues(state: str = "open", limit: int = 50) -> dict:
    """
    Fetch Linear issues by state type.

    state: 'open' (backlog + unstarted + started), 'in_progress' (started),
           'todo' (unstarted), 'done' (completed), 'all' (everything)
    """
    type_map = {
        "open": '["backlog", "unstarted", "started"]',
        "in_progress": '["started"]',
        "todo": '["unstarted"]',
        "backlog": '["backlog"]',
        "done": '["completed", "canceled"]',
        "all": '["backlog", "unstarted", "started", "completed", "canceled"]',
    }
    types = type_map.get(state, type_map["open"])

    query = """
    query($first: Int!) {
      issues(
        filter: { state: { type: { in: STATE_TYPES } } }
        first: $first
      ) {
        nodes {
          identifier title state { name type }
          priority assignee { name email }
          dueDate labels { nodes { name } }
          createdAt updatedAt url
          team { key name }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
    """.replace("STATE_TYPES", types)

    result = linear_query(query, {"first": limit})
    issues = result.get("data", {}).get("issues", {}).get("nodes", [])

    # Group by state type
    by_type = {"backlog": [], "unstarted": [], "started": [], "completed": [], "canceled": [], "other": []}
    for i in issues:
        t = i.get("state", {}).get("type", "other")
        by_type.get(t, by_type["other"]).append(i)

    return {
        "tool": "linear_issues",
        "state": state,
        "total": len(issues),
        "by_state": {
            "Backlog": [i["identifier"] + " — " + i["title"] for i in by_type["backlog"]],
            "Todo (unstarted)": [i["identifier"] + " — " + i["title"] for i in by_type["unstarted"]],
            "In Progress (started)": [i["identifier"] + " — " + i["title"] for i in by_type["started"]],
            "Done (completed)": [i["identifier"] + " — " + i["title"] for i in by_type["completed"]],
            "Canceled": [i["identifier"] + " — " + i["title"] for i in by_type["canceled"]],
        },
        "raw": issues
    }


# ─────────────────────────────────────────────
# TOOL: linear_mine — My assigned issues
# ─────────────────────────────────────────────

def linear_mine() -> dict:
    """Fetch issues assigned to the current viewer."""
    query = """
    {
      viewer {
        assignedIssues(first: 50) {
          nodes {
            identifier title state { name type }
            priority dueDate labels { nodes { name } }
            team { key name } url
          }
        }
      }
    }
    """
    result = linear_query(query)
    issues = result.get("data", {}).get("viewer", {}).get("assignedIssues", {}).get("nodes", [])

    by_state = {"unstarted": [], "started": [], "completed": [], "other": []}
    for i in issues:
        t = i.get("state", {}).get("type", "other")
        by_state.get(t, by_state["other"]).append(i)

    return {
        "tool": "linear_mine",
        "total": len(issues),
        "by_state": {k: [x["identifier"] + " — " + x["title"] for x in v]
                     for k, v in by_state.items() if v},
        "raw": issues
    }


# ─────────────────────────────────────────────
# TOOL: linear_blockers — Unassigned issues
# ─────────────────────────────────────────────

def linear_blockers(days: int = 7) -> dict:
    """Fetch unassigned open issues (potential blockers)."""
    query = """
    query($first: Int!) {
      issues(
        filter: {
          state: { type: { in: ["unstarted", "started"] } }
          assignee: { eq: null }
        }
        first: $first
      ) {
        nodes {
          identifier title state { name type }
          priority createdAt team { key name } url
        }
      }
    }
    """
    result = linear_query(query, {"first": 50})
    issues = result.get("data", {}).get("issues", {}).get("nodes", [])

    # Filter to recent
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for i in issues:
        try:
            created = datetime.fromisoformat(i["createdAt"].replace("Z", "+00:00"))
            if created > cutoff:
                recent.append(i)
        except Exception:
            recent.append(i)

    return {
        "tool": "linear_blockers",
        "unassigned_count": len(issues),
        "recent_unassigned": len(recent),
        "issues": [i["identifier"] + " — " + i["title"] for i in recent],
        "raw": recent
    }


# ─────────────────────────────────────────────
# TOOL: linear_person_tasks — Tasks by person
# ─────────────────────────────────────────────

def linear_person_tasks(email: str) -> dict:
    """Fetch open issues assigned to a specific person by email."""
    query = """
    query($filter: IssueFilterInput, $first: Int!) {
      issues(filter: $filter, first: $first) {
        nodes {
          identifier title state { name type }
          priority dueDate team { key name } url
        }
      }
    }
    """
    variables = {
        "filter": {
            "assignee": {"email": {"eq": email}},
            "state": {"type": {"in": ["unstarted", "started"]}}
        },
        "first": 30
    }
    result = linear_query(query, variables)
    issues = result.get("data", {}).get("issues", {}).get("nodes", [])

    return {
        "tool": "linear_person_tasks",
        "email": email,
        "count": len(issues),
        "issues": [i["identifier"] + " [" + i.get("state", {}).get("name", "") + "] " + i["title"] for i in issues],
        "raw": issues
    }


# ─────────────────────────────────────────────
# TOOL: linear_summary — Full workspace snapshot
# ─────────────────────────────────────────────

def linear_summary() -> dict:
    """Get full Linear workspace summary."""
    workspace = linear_workspace()

    # Teams
    teams_result = linear_query("{ teams { nodes { id name key } } }")
    teams = teams_result.get("data", {}).get("teams", {}).get("nodes", [])

    # Open issues
    open_result = linear_issues("open", 100)
    todo_count = len(open_result.get("by_state", {}).get("Todo (unstarted)", []))
    inprog_count = len(open_result.get("by_state", {}).get("In Progress (started)", []))

    # Completed
    done_result = linear_issues("done", 20)
    done_count = len(done_result.get("by_state", {}).get("Done (completed)", []))

    # My issues
    my = linear_mine()

    # Blockers
    blockers = linear_blockers(7)

    return {
        "tool": "linear_summary",
        "workspace": workspace,
        "teams": [{"name": t["name"], "key": t["key"]} for t in teams],
        "metrics": {
            "todo": todo_count,
            "in_progress": inprog_count,
            "completed_recent": done_count,
        },
        "my_tasks": my.get("total", 0),
        "blockers": blockers.get("recent_unassigned", 0),
        "todo_items": open_result.get("by_state", {}).get("Todo (unstarted)", [])[:10],
        "in_progress_items": open_result.get("by_state", {}).get("In Progress (started)", [])[:10],
    }


# ─────────────────────────────────────────────
# TOOL: linear_sync — Sync to Obsidian
# ─────────────────────────────────────────────

def linear_sync() -> dict:
    """Fetch Linear data and save to Obsidian vault."""
    vault = vault_path()
    insights_dir = Path(vault) / "insights"
    insights_dir.mkdir(parents=True, exist_ok=True)

    summary = linear_summary()
    output_path = insights_dir / "linear-overview.md"

    content = f"""# Linear Overview — {summary['workspace']}

> Atualizado: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Métricas

| Estado | Count |
|--------|-------|
| 📋 Todo | {summary['metrics']['todo']} |
| 🔄 In Progress | {summary['metrics']['in_progress']} |
| ✅ Done (recento) | {summary['metrics']['completed_recent']} |
| ⚠️ Blockers (sem assignee) | {summary['blockers']} |

## As Minhas Tarefas

Total: **{summary['my_tasks']}** issues atribuídos

## Issues em Todo (top 10)

"""
    for item in summary.get("todo_items", []):
        content += f"- {item}\n"

    content += "\n## Issues em In Progress (top 10)\n\n"
    for item in summary.get("in_progress_items", []):
        content += f"- {item}\n"

    with open(output_path, "w") as f:
        f.write(content)

    return {
        "tool": "linear_sync",
        "saved_to": str(output_path),
        "summary": summary
    }


# ─────────────────────────────────────────────
# TOOL: linear_project_health — Project analytics
# ─────────────────────────────────────────────

def linear_project_health(days: int = 30) -> dict:
    """
    Analyze Linear projects with health scores.

    Returns:
    - Issues grouped by project/team
    - Project health metrics (velocity, staleness, completion rate)
    - Risk indicators
    """
    # Fetch all projects
    projects_query = """
    {
      projects(first: 50) {
        nodes {
          id name state
          lead { name email }
          targetDate startDate
          issues {
            nodes {
              identifier title state { name type }
              createdAt updatedAt completedAt
              priority assignee { name }
            }
          }
        }
      }
    }
    """

    result = linear_query(projects_query)
    projects = result.get("data", {}).get("projects", {}).get("nodes", [])

    if not projects:
        # Fallback: group by team if no projects
        return _analyze_by_teams(days)

    project_health = []
    now = datetime.now()
    cutoff = now - timedelta(days=days)

    for project in projects:
        issues = project.get("issues", {}).get("nodes", [])

        if not issues:
            continue

        # Calculate metrics
        total_issues = len(issues)
        completed = [i for i in issues if i.get("state", {}).get("type") == "completed"]
        in_progress = [i for i in issues if i.get("state", {}).get("type") == "started"]
        todo = [i for i in issues if i.get("state", {}).get("type") == "unstarted"]

        completion_rate = (len(completed) / total_issues * 100) if total_issues > 0 else 0

        # Calculate staleness (issues not updated in 7+ days)
        stale_cutoff = now - timedelta(days=7)
        stale_issues = []
        for issue in in_progress + todo:
            try:
                updated = datetime.fromisoformat(issue.get("updatedAt", "").replace("Z", "+00:00"))
                if updated.replace(tzinfo=None) < stale_cutoff:
                    stale_issues.append(issue)
            except:
                pass

        staleness_rate = (len(stale_issues) / len(in_progress + todo) * 100) if (in_progress + todo) else 0

        # Calculate velocity (issues completed in last N days)
        recent_completed = []
        for issue in completed:
            try:
                completed_at = issue.get("completedAt")
                if completed_at:
                    completed_date = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                    if completed_date.replace(tzinfo=None) > cutoff:
                        recent_completed.append(issue)
            except:
                pass

        velocity = len(recent_completed) / days  # issues/day

        # Calculate health score (0-100)
        health_score = (
            completion_rate * 0.4 +  # 40% weight
            (100 - staleness_rate) * 0.3 +  # 30% weight
            min(velocity * 10, 30)  # 30% weight (capped at 30)
        )

        # Determine health status
        if health_score >= 80:
            health_status = "healthy"
            health_emoji = "🟢"
        elif health_score >= 60:
            health_status = "moderate"
            health_emoji = "🟡"
        else:
            health_status = "at_risk"
            health_emoji = "🔴"

        # Risk factors
        risks = []
        if staleness_rate > 50:
            risks.append("High staleness - many issues not updated in 7+ days")
        if len(in_progress) > len(completed) * 2:
            risks.append("Too much WIP - more in progress than completed")
        if completion_rate < 30 and total_issues > 5:
            risks.append("Low completion rate - less than 30% done")
        if velocity < 0.5:
            risks.append("Low velocity - less than 0.5 issues/day")

        project_data = {
            "name": project.get("name"),
            "id": project.get("id"),
            "state": project.get("state"),
            "lead": project.get("lead", {}).get("name", "Unassigned"),
            "target_date": project.get("targetDate"),
            "start_date": project.get("startDate"),
            "metrics": {
                "total_issues": total_issues,
                "completed": len(completed),
                "in_progress": len(in_progress),
                "todo": len(todo),
                "completion_rate": round(completion_rate, 1),
                "staleness_rate": round(staleness_rate, 1),
                "velocity": round(velocity, 2),
                "stale_count": len(stale_issues)
            },
            "health": {
                "score": round(health_score, 1),
                "status": health_status,
                "emoji": health_emoji
            },
            "risks": risks,
            "top_stale_issues": [
                i.get("identifier") + " — " + i.get("title")
                for i in stale_issues[:3]
            ]
        }

        project_health.append(project_data)

    # Sort by health score (lowest first - show problems)
    project_health.sort(key=lambda x: x["health"]["score"])

    return {
        "tool": "linear_project_health",
        "timestamp": now.isoformat(),
        "period_days": days,
        "total_projects": len(project_health),
        "projects": project_health,
        "summary": _generate_project_insights(project_health)
    }


def _analyze_by_teams(days: int) -> dict:
    """Fallback: analyze by teams if no projects exist."""
    # Get all teams
    teams_query = "{ teams { nodes { id name key } } }"
    result = linear_query(teams_query)
    teams = result.get("data", {}).get("teams", {}).get("nodes", [])

    team_health = []
    now = datetime.now()

    for team in teams:
        team_key = team.get("key")

        # Get team issues
        issues_query = f"""
        query($first: Int!) {{
          team(id: "{team.get('id')}") {{
            issues(first: $first) {{
              nodes {{
                identifier title state {{ name type }}
                createdAt updatedAt completedAt
              }}
            }}
          }}
        }}
        """

        result = linear_query(issues_query, {"first": 100})
        issues = result.get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])

        if not issues:
            continue

        # Same metrics calculation as projects
        total = len(issues)
        completed = [i for i in issues if i.get("state", {}).get("type") == "completed"]
        completion_rate = (len(completed) / total * 100) if total > 0 else 0

        team_health.append({
            "name": team.get("name"),
            "key": team_key,
            "metrics": {
                "total_issues": total,
                "completed": len(completed),
                "completion_rate": round(completion_rate, 1)
            }
        })

    return {
        "tool": "linear_project_health",
        "timestamp": now.isoformat(),
        "period_days": days,
        "mode": "teams",
        "total_teams": len(team_health),
        "teams": team_health,
        "summary": {"message": "Analyzed by teams (no projects found)"}
    }


def _generate_project_insights(projects: list) -> dict:
    """Generate insights from project health data."""
    if not projects:
        return {"message": "No projects to analyze"}

    at_risk = [p for p in projects if p["health"]["status"] == "at_risk"]
    moderate = [p for p in projects if p["health"]["status"] == "moderate"]
    healthy = [p for p in projects if p["health"]["status"] == "healthy"]

    insights = {
        "at_risk_count": len(at_risk),
        "moderate_count": len(moderate),
        "healthy_count": len(healthy),
        "avg_health_score": round(sum(p["health"]["score"] for p in projects) / len(projects), 1),
        "recommendations": []
    }

    if at_risk:
        insights["recommendations"].append({
            "priority": "high",
            "message": f"{len(at_risk)} project(s) at risk",
            "action": f"Review: {', '.join(p['name'] for p in at_risk[:3])}"
        })

    if moderate:
        insights["recommendations"].append({
            "priority": "medium",
            "message": f"{len(moderate)} project(s) need attention",
            "action": "Monitor staleness and velocity"
        })

    if not insights["recommendations"]:
        insights["recommendations"].append({
            "priority": "low",
            "message": "All projects healthy",
            "action": "Keep up the good work!"
        })

    return insights


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "issues":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        result = linear_issues(state)
    elif cmd == "mine":
        result = linear_mine()
    elif cmd == "blockers":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        result = linear_blockers(days)
    elif cmd == "person":
        email = sys.argv[2] if len(sys.argv) > 2 else ""
        result = linear_person_tasks(email)
    elif cmd == "sync":
        result = linear_sync()
    elif cmd == "summary":
        result = linear_summary()
    elif cmd == "project-health":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = linear_project_health(days)
    else:
        result = {"error": f"Unknown command: {cmd}. Available: issues, mine, blockers, person, sync, summary, project-health"}

    print(json.dumps(result, indent=2, default=str))