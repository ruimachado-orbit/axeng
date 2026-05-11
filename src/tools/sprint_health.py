#!/usr/bin/env python3
"""
Sprint Health Analysis
Analyzes current sprint using Linear cycles/projects and GitHub data.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get
from tools.linear_tool import linear_query, load_env
from tools.github_activity import gh_api


def get_current_cycle() -> dict:
    """Get current active Linear cycle (sprint)."""
    query = """
    {
      cycles(
        filter: { isActive: { eq: true } }
        first: 1
      ) {
        nodes {
          id name number
          startsAt endsAt
          completedAt
          progress
          scopeHistory
          issues {
            nodes {
              identifier title state { name type }
              priority estimate
              completedAt
              createdAt updatedAt
              assignee { name email }
              team { name key }
            }
          }
        }
      }
    }
    """

    result = linear_query(query)
    cycles = result.get("data", {}).get("cycles", {}).get("nodes", [])

    if not cycles:
        return {
            "error": "No active cycle found",
            "hint": "Create a cycle in Linear or mark one as active"
        }

    return cycles[0]


def calculate_sprint_metrics(cycle: dict) -> dict:
    """Calculate sprint health metrics from cycle data."""
    issues = cycle.get("issues", {}).get("nodes", [])

    if not issues:
        return {
            "total_issues": 0,
            "completed": 0,
            "in_progress": 0,
            "todo": 0,
            "completion_rate": 0,
            "velocity": 0,
            "estimated_points": 0,
            "completed_points": 0
        }

    # Count by state
    completed = [i for i in issues if i.get("state", {}).get("type") == "completed"]
    in_progress = [i for i in issues if i.get("state", {}).get("type") == "started"]
    todo = [i for i in issues if i.get("state", {}).get("type") in ["unstarted", "backlog"]]

    # Calculate points (estimates)
    total_points = sum(i.get("estimate", 0) or 0 for i in issues)
    completed_points = sum(i.get("estimate", 0) or 0 for i in completed)

    # Calculate velocity (points per day)
    try:
        starts_at = datetime.fromisoformat(cycle.get("startsAt", "").replace("Z", "+00:00"))
        now = datetime.now()
        days_elapsed = max(1, (now - starts_at.replace(tzinfo=None)).days)
        velocity = completed_points / days_elapsed if days_elapsed > 0 else 0
    except:
        velocity = 0
        days_elapsed = 0

    return {
        "total_issues": len(issues),
        "completed": len(completed),
        "in_progress": len(in_progress),
        "todo": len(todo),
        "completion_rate": (len(completed) / len(issues) * 100) if issues else 0,
        "velocity": round(velocity, 2),
        "estimated_points": total_points,
        "completed_points": completed_points,
        "days_elapsed": days_elapsed,
        "issues_by_state": {
            "completed": completed,
            "in_progress": in_progress,
            "todo": todo
        }
    }


def predict_sprint_completion(cycle: dict, metrics: dict) -> dict:
    """Predict if sprint will complete on time."""
    try:
        starts_at = datetime.fromisoformat(cycle.get("startsAt", "").replace("Z", "+00:00"))
        ends_at = datetime.fromisoformat(cycle.get("endsAt", "").replace("Z", "+00:00"))
        now = datetime.now()

        starts_at = starts_at.replace(tzinfo=None)
        ends_at = ends_at.replace(tzinfo=None)

        total_days = (ends_at - starts_at).days
        days_elapsed = (now - starts_at).days
        days_remaining = (ends_at - now).days

        # Progress percentage
        time_progress = (days_elapsed / total_days * 100) if total_days > 0 else 0
        work_progress = metrics["completion_rate"]

        # Prediction
        on_track = work_progress >= time_progress - 10  # 10% tolerance

        # Calculate needed velocity
        remaining_points = metrics["estimated_points"] - metrics["completed_points"]
        needed_velocity = remaining_points / days_remaining if days_remaining > 0 else 0
        current_velocity = metrics["velocity"]

        # Status
        if on_track and current_velocity >= needed_velocity:
            status = "on_track"
            emoji = "🟢"
            message = "Sprint is on track"
        elif work_progress >= time_progress - 20:
            status = "at_risk"
            emoji = "🟡"
            message = "Sprint slightly behind"
        else:
            status = "off_track"
            emoji = "🔴"
            message = "Sprint significantly behind"

        return {
            "status": status,
            "emoji": emoji,
            "message": message,
            "time_progress": round(time_progress, 1),
            "work_progress": round(work_progress, 1),
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "total_days": total_days,
            "current_velocity": current_velocity,
            "needed_velocity": round(needed_velocity, 2),
            "on_track": on_track
        }
    except Exception as e:
        return {
            "error": f"Could not predict completion: {str(e)}"
        }


def get_sprint_insights(metrics: dict, prediction: dict) -> list:
    """Generate actionable insights from sprint data."""
    insights = []

    # High WIP
    if metrics["in_progress"] > metrics["completed"]:
        insights.append({
            "type": "warning",
            "category": "high_wip",
            "message": f"{metrics['in_progress']} issues in progress vs {metrics['completed']} completed",
            "action": "Focus on completing existing work before starting new issues"
        })

    # Low velocity
    if prediction.get("current_velocity", 0) < prediction.get("needed_velocity", 0):
        insights.append({
            "type": "critical",
            "category": "low_velocity",
            "message": f"Current velocity {prediction['current_velocity']} < needed {prediction['needed_velocity']}",
            "action": "Consider descoping or adding resources"
        })

    # Behind schedule
    if prediction.get("status") == "off_track":
        behind_pct = prediction["time_progress"] - prediction["work_progress"]
        insights.append({
            "type": "critical",
            "category": "behind_schedule",
            "message": f"Sprint is {behind_pct:.0f}% behind schedule",
            "action": "Review sprint goals with team immediately"
        })

    # No issues in progress
    if metrics["in_progress"] == 0 and metrics["todo"] > 0:
        insights.append({
            "type": "warning",
            "category": "no_wip",
            "message": "No issues currently in progress",
            "action": "Team may be blocked or need work assignment"
        })

    # Healthy
    if not insights and prediction.get("status") == "on_track":
        insights.append({
            "type": "success",
            "category": "healthy",
            "message": "Sprint is healthy and on track",
            "action": "Keep up the good work!"
        })

    return insights


def sprint_health() -> dict:
    """Get comprehensive sprint health analysis."""
    # Get current cycle
    cycle = get_current_cycle()

    if "error" in cycle:
        return {
            "tool": "sprint_health",
            "error": cycle["error"],
            "hint": cycle.get("hint")
        }

    # Calculate metrics
    metrics = calculate_sprint_metrics(cycle)

    # Predict completion
    prediction = predict_sprint_completion(cycle, metrics)

    # Get insights
    insights = get_sprint_insights(metrics, prediction)

    return {
        "tool": "sprint_health",
        "timestamp": datetime.now().isoformat(),
        "cycle": {
            "name": cycle.get("name"),
            "number": cycle.get("number"),
            "starts_at": cycle.get("startsAt"),
            "ends_at": cycle.get("endsAt"),
            "progress": cycle.get("progress", 0)
        },
        "metrics": metrics,
        "prediction": prediction,
        "insights": insights,
        "burndown": _calculate_burndown(cycle, metrics)
    }


def _calculate_burndown(cycle: dict, metrics: dict) -> list:
    """Calculate simple burndown data points."""
    try:
        starts_at = datetime.fromisoformat(cycle.get("startsAt", "").replace("Z", "+00:00"))
        ends_at = datetime.fromisoformat(cycle.get("endsAt", "").replace("Z", "+00:00"))
        now = datetime.now()

        starts_at = starts_at.replace(tzinfo=None)
        ends_at = ends_at.replace(tzinfo=None)

        total_days = (ends_at - starts_at).days
        days_elapsed = (now - starts_at).days

        # Ideal burndown
        total_points = metrics["estimated_points"]
        completed_points = metrics["completed_points"]
        remaining_points = total_points - completed_points

        # Simple 3-point burndown: start, today, end
        return [
            {
                "day": 0,
                "date": starts_at.date().isoformat(),
                "ideal_remaining": total_points,
                "actual_remaining": total_points
            },
            {
                "day": days_elapsed,
                "date": now.date().isoformat(),
                "ideal_remaining": total_points * (total_days - days_elapsed) / total_days if total_days > 0 else 0,
                "actual_remaining": remaining_points
            },
            {
                "day": total_days,
                "date": ends_at.date().isoformat(),
                "ideal_remaining": 0,
                "actual_remaining": 0  # projection
            }
        ]
    except:
        return []


def sprint_velocity(cycles: int = 5) -> dict:
    """Get historical sprint velocity data."""
    query = f"""
    {{
      cycles(
        filter: {{ isActive: {{ eq: false }} }}
        orderBy: {{ direction: DESC, field: number }}
        first: {cycles}
      ) {{
        nodes {{
          id name number
          startsAt endsAt completedAt
          progress
          issues {{
            nodes {{
              estimate
              state {{ type }}
            }}
          }}
        }}
      }}
    }}
    """

    result = linear_query(query)
    cycles_data = result.get("data", {}).get("cycles", {}).get("nodes", [])

    velocity_history = []

    for cycle in cycles_data:
        issues = cycle.get("issues", {}).get("nodes", [])
        completed = [i for i in issues if i.get("state", {}).get("type") == "completed"]

        total_points = sum(i.get("estimate", 0) or 0 for i in issues)
        completed_points = sum(i.get("estimate", 0) or 0 for i in completed)

        try:
            starts_at = datetime.fromisoformat(cycle.get("startsAt", "").replace("Z", "+00:00"))
            ends_at = datetime.fromisoformat(cycle.get("endsAt", "").replace("Z", "+00:00"))
            duration_days = (ends_at.replace(tzinfo=None) - starts_at.replace(tzinfo=None)).days
        except:
            duration_days = 14  # default 2 weeks

        velocity_history.append({
            "cycle": cycle.get("name"),
            "number": cycle.get("number"),
            "completed_points": completed_points,
            "total_points": total_points,
            "completion_rate": (completed_points / total_points * 100) if total_points > 0 else 0,
            "velocity_per_day": completed_points / duration_days if duration_days > 0 else 0,
            "duration_days": duration_days
        })

    # Calculate average velocity
    if velocity_history:
        avg_velocity = sum(v["velocity_per_day"] for v in velocity_history) / len(velocity_history)
        avg_completion = sum(v["completion_rate"] for v in velocity_history) / len(velocity_history)
    else:
        avg_velocity = 0
        avg_completion = 0

    return {
        "tool": "sprint_velocity",
        "timestamp": datetime.now().isoformat(),
        "cycles_analyzed": len(velocity_history),
        "average_velocity": round(avg_velocity, 2),
        "average_completion_rate": round(avg_completion, 1),
        "history": velocity_history,
        "trend": _calculate_trend(velocity_history)
    }


def _calculate_trend(history: list) -> str:
    """Calculate if velocity is improving or declining."""
    if len(history) < 2:
        return "insufficient_data"

    # Compare recent half vs older half
    mid = len(history) // 2
    recent_avg = sum(v["velocity_per_day"] for v in history[:mid]) / mid
    older_avg = sum(v["velocity_per_day"] for v in history[mid:]) / (len(history) - mid)

    if recent_avg > older_avg * 1.1:
        return "improving"
    elif recent_avg < older_avg * 0.9:
        return "declining"
    else:
        return "stable"


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"

    if cmd == "health":
        result = sprint_health()
    elif cmd == "velocity":
        cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        result = sprint_velocity(cycles)
    else:
        result = {"error": f"Unknown command: {cmd}. Available: health, velocity"}

    print(json.dumps(result, indent=2, default=str))
