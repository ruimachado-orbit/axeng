#!/usr/bin/env python3
"""
Weekly Report Generator
Generates comprehensive weekly summary using all available data sources.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get
from tools.linear_tool import linear_query, linear_summary
from tools.github_activity import github_activity
from tools.sprint_health import sprint_health, sprint_velocity
from tools.dora_metrics import dora_metrics
from tools.vacations import who_is_ooo_today


def _load_local_env() -> None:
    """Load simple KEY=VALUE pairs from local .env files into os.environ."""
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
        Path(os.getenv("AXENG_HOME", "~/.axeng")).expanduser() / ".env",
    ]
    for path in env_paths:
        if not path.exists():
            continue
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        except Exception:
            continue


def generate_weekly_report(send: bool = False) -> dict:
    """Generate comprehensive weekly report."""
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    print("📊 Generating weekly report...", file=sys.stderr)

    # Collect data from all sources
    report_data = {
        "generated_at": now.isoformat(),
        "week_ending": now.date().isoformat(),
        "week_starting": week_ago.date().isoformat()
    }

    # 1. Sprint Health
    print("  🔍 Analyzing sprint health...", file=sys.stderr)
    try:
        sprint_data = sprint_health()
        report_data["sprint"] = sprint_data
    except Exception as e:
        report_data["sprint"] = {"error": str(e)}

    # 2. DORA Metrics
    print("  📈 Calculating DORA metrics...", file=sys.stderr)
    try:
        dora_data = dora_metrics(days=30)
        report_data["dora"] = dora_data
    except Exception as e:
        report_data["dora"] = {"error": str(e)}

    # 3. GitHub Activity
    print("  🔧 Fetching GitHub activity...", file=sys.stderr)
    try:
        github_data = github_activity(person=None, days=7)
        report_data["github"] = {
            "commits_count": len(github_data.get("commits", [])),
            "prs_merged": len(github_data.get("pulls", [])),
            "reviews": len(github_data.get("reviews", [])),
            "top_contributors": _get_top_contributors(github_data)
        }
    except Exception as e:
        report_data["github"] = {"error": str(e)}

    # 4. Linear Summary
    print("  📋 Getting Linear summary...", file=sys.stderr)
    try:
        linear_data = linear_summary()
        report_data["linear"] = {
            "todo": linear_data.get("metrics", {}).get("todo", 0),
            "in_progress": linear_data.get("metrics", {}).get("in_progress", 0),
            "completed": linear_data.get("metrics", {}).get("completed_recent", 0),
            "blockers": linear_data.get("blockers", 0)
        }
    except Exception as e:
        report_data["linear"] = {"error": str(e)}

    # 5. Who's OOO
    print("  🏖️  Checking vacations...", file=sys.stderr)
    try:
        ooo_data = who_is_ooo_today()
        report_data["ooo"] = {
            "count": ooo_data.get("total", 0),
            "people": [v.get("person") for v in ooo_data.get("vacations", [])]
        }
    except Exception as e:
        report_data["ooo"] = {"error": str(e)}

    # 6. Velocity Trend
    print("  ⚡ Analyzing velocity...", file=sys.stderr)
    try:
        velocity_data = sprint_velocity(cycles=5)
        report_data["velocity"] = {
            "current": velocity_data.get("average_velocity", 0),
            "trend": velocity_data.get("trend", "stable"),
            "completion_rate": velocity_data.get("average_completion_rate", 0)
        }
    except Exception as e:
        report_data["velocity"] = {"error": str(e)}

    # Generate formatted report
    formatted_report = _format_report(report_data)
    report_data["formatted_text"] = formatted_report
    report_data["formatted_html"] = _format_report_html(report_data)

    # Send if requested
    if send:
        success = _send_report(formatted_report, report_data)
        report_data["sent"] = success

    print("✅ Report generated!", file=sys.stderr)

    return {
        "tool": "weekly_report",
        **report_data
    }


def _get_top_contributors(github_data: dict) -> list:
    """Extract top contributors from GitHub data."""
    contributors = {}

    for commit in github_data.get("commits", []):
        author = commit.get("author", "Unknown")
        contributors[author] = contributors.get(author, 0) + 1

    # Sort by commit count
    sorted_contributors = sorted(contributors.items(), key=lambda x: x[1], reverse=True)
    return [{"name": name, "commits": count} for name, count in sorted_contributors[:5]]


def _format_report(data: dict) -> str:
    """Format report as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 WEEKLY ENGINEERING REPORT")
    lines.append("=" * 60)
    lines.append(f"Week Ending: {data.get('week_ending')}")
    lines.append(f"Generated: {data.get('generated_at')}")
    lines.append("")

    # Sprint Health
    sprint = data.get("sprint", {})
    if "error" not in sprint:
        lines.append("🎯 SPRINT HEALTH")
        lines.append("-" * 60)
        cycle = sprint.get("cycle", {})
        metrics = sprint.get("metrics", {})
        prediction = sprint.get("prediction", {})

        lines.append(f"Sprint: {cycle.get('name', 'N/A')}")
        lines.append(f"Status: {prediction.get('emoji', '')} {prediction.get('message', 'N/A')}")
        lines.append(f"Progress: {metrics.get('completion_rate', 0):.1f}% ({metrics.get('completed', 0)}/{metrics.get('total_issues', 0)} issues)")
        lines.append(f"Velocity: {metrics.get('velocity', 0)} points/day")
        lines.append("")

    # DORA Metrics
    dora = data.get("dora", {})
    if "error" not in dora:
        lines.append("📈 DORA METRICS (Engineering Excellence)")
        lines.append("-" * 60)
        metrics = dora.get("metrics", {})

        deploy = metrics.get("deployment_frequency", {})
        lines.append(f"Deployment Frequency: {deploy.get('emoji', '')} {deploy.get('per_week', 0):.1f} deploys/week ({deploy.get('dora_tier', 'N/A')})")

        lead = metrics.get("lead_time", {})
        lines.append(f"Lead Time: {lead.get('emoji', '')} {lead.get('average_days', 0):.1f} days ({lead.get('dora_tier', 'N/A')})")

        mttr = metrics.get("mttr", {})
        if "error" not in mttr:
            lines.append(f"MTTR: {mttr.get('emoji', '')} {mttr.get('average_hours', 0):.1f} hours ({mttr.get('dora_tier', 'N/A')})")

        failure = metrics.get("change_failure_rate", {})
        lines.append(f"Change Failure Rate: {failure.get('emoji', '')} {failure.get('failure_rate_pct', 0):.1f}% ({failure.get('dora_tier', 'N/A')})")

        lines.append(f"\nOverall DORA Tier: {dora.get('overall_tier', 'N/A')}")
        lines.append("")

    # GitHub Activity
    github = data.get("github", {})
    if "error" not in github:
        lines.append("🔧 GITHUB ACTIVITY (Last 7 Days)")
        lines.append("-" * 60)
        lines.append(f"Commits: {github.get('commits_count', 0)}")
        lines.append(f"PRs Merged: {github.get('prs_merged', 0)}")
        lines.append(f"Reviews: {github.get('reviews', 0)}")

        top = github.get("top_contributors", [])
        if top:
            lines.append("\nTop Contributors:")
            for contrib in top[:3]:
                lines.append(f"  • {contrib.get('name')}: {contrib.get('commits')} commits")
        lines.append("")

    # Linear Summary
    linear = data.get("linear", {})
    if "error" not in linear:
        lines.append("📋 LINEAR ISSUES")
        lines.append("-" * 60)
        lines.append(f"Todo: {linear.get('todo', 0)}")
        lines.append(f"In Progress: {linear.get('in_progress', 0)}")
        lines.append(f"Completed (week): {linear.get('completed', 0)}")
        lines.append(f"Blockers: {linear.get('blockers', 0)}")
        lines.append("")

    # Velocity Trend
    velocity = data.get("velocity", {})
    if "error" not in velocity:
        lines.append("⚡ VELOCITY TREND")
        lines.append("-" * 60)
        lines.append(f"Current: {velocity.get('current', 0):.2f} points/day")
        lines.append(f"Trend: {velocity.get('trend', 'N/A').title()}")
        lines.append(f"Completion Rate: {velocity.get('completion_rate', 0):.1f}%")
        lines.append("")

    # OOO
    ooo = data.get("ooo", {})
    if "error" not in ooo and ooo.get("count", 0) > 0:
        lines.append("🏖️  OUT OF OFFICE")
        lines.append("-" * 60)
        lines.append(f"{ooo.get('count')} person(s) OOO today:")
        for person in ooo.get("people", []):
            lines.append(f"  • {person}")
        lines.append("")

    # Summary & Recommendations
    lines.append("💡 KEY INSIGHTS")
    lines.append("-" * 60)
    insights = _generate_insights(data)
    for insight in insights:
        lines.append(f"• {insight}")
    lines.append("")

    lines.append("=" * 60)
    lines.append("Generated by Axeng - Engineering Manager Accelerator")
    lines.append("=" * 60)

    return "\n".join(lines)


def _format_report_html(data: dict) -> str:
    """Format report as HTML for email."""
    # Simplified HTML version
    text_report = _format_report(data)
    html = f"""
    <html>
    <body style="font-family: monospace; background-color: #1e1e1e; color: #d4d4d4; padding: 20px;">
    <pre style="color: #d4d4d4;">
{text_report}
    </pre>
    </body>
    </html>
    """
    return html


def _generate_insights(data: dict) -> list:
    """Generate key insights from report data."""
    insights = []

    # Sprint health insights
    sprint = data.get("sprint", {})
    prediction = sprint.get("prediction", {})
    if prediction.get("status") == "off_track":
        insights.append(f"⚠️  Sprint is off track - review scope or add resources")
    elif prediction.get("status") == "on_track":
        insights.append("✅ Sprint is on track to complete on time")

    # DORA insights
    dora = data.get("dora", {})
    if dora.get("overall_tier") in ["Elite", "High"]:
        insights.append(f"🌟 DORA metrics are {dora.get('overall_tier')} tier - excellent!")
    elif dora.get("overall_tier") == "Low":
        summary = dora.get("metrics", {}).get("summary", {})
        priority = summary.get("top_priority")
        if priority:
            insights.append(f"🔴 Focus area: {priority}")

    # Velocity insights
    velocity = data.get("velocity", {})
    if velocity.get("trend") == "improving":
        insights.append("📈 Team velocity is improving")
    elif velocity.get("trend") == "declining":
        insights.append("📉 Team velocity is declining - investigate blockers")

    # Blockers
    linear = data.get("linear", {})
    if linear.get("blockers", 0) > 5:
        insights.append(f"⚠️  {linear.get('blockers')} unassigned blockers need attention")

    if not insights:
        insights.append("All metrics look healthy - keep up the good work!")

    return insights


def _send_report(report_text: str, data: dict) -> bool:
    """Send report via configured channel (Telegram, Email, etc.)."""
    try:
        import subprocess

        _load_local_env()
        delivered = False
        report_body = report_text[:4000]

        # Try Telegram first
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")

        if telegram_token and telegram_chat:
            try:
                result = subprocess.run(
                    [
                        "curl", "-s", "-X", "POST",
                        f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                        "-d", f"chat_id={telegram_chat}",
                        "-d", f"text={report_body}",  # Telegram limit
                        "-d", "parse_mode=HTML"
                    ],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print("💬 Sent via Telegram", file=sys.stderr)
                    delivered = True
                else:
                    print(f"⚠️  Telegram delivery failed: {result.stderr or result.stdout}", file=sys.stderr)
            except Exception as exc:
                print(f"⚠️  Telegram delivery failed: {exc}", file=sys.stderr)

        slack_webhook = (
            os.getenv("SLACK_WEBHOOK_URL")
            or get("reporting.webhook_url")
            or get("steering.webhook_url")
        )
        if slack_webhook:
            try:
                payload = json.dumps({"text": report_body}).encode("utf-8")
                req = urllib.request.Request(
                    slack_webhook,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if 200 <= getattr(resp, "status", 200) < 300:
                        print("💬 Sent via Slack", file=sys.stderr)
                        delivered = True
                    else:
                        print(f"⚠️  Slack delivery failed with status {getattr(resp, 'status', 'unknown')}", file=sys.stderr)
            except Exception as exc:
                print(f"⚠️  Slack delivery failed: {exc}", file=sys.stderr)

        if delivered:
            return True

        # TODO: Add email sending via gmail_script
        # For now, just save to file
        output_dir = Path.home() / ".axeng" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"weekly_report_{timestamp}.txt"

        with open(report_file, "w") as f:
            f.write(report_text)

        print(f"📄 Report saved to: {report_file}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"❌ Failed to send report: {e}", file=sys.stderr)
        return False


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate weekly engineering report")
    parser.add_argument("--send", action="store_true", help="Send report via Telegram/Email")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = generate_weekly_report(send=args.send)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(result.get("formatted_text", ""))
