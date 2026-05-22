"""
Demo / Showcase Data Provider for Axeng
=========================================

Provides mock fallback data so Axeng works without any API keys configured.
Used when Linear, GitHub, and other integrations are not set up.

All dates are computed relative to the current week (Monday-Friday)
so the demo data always looks fresh.

Usage:
    from demo_data import DemoProvider

    provider = DemoProvider()
    issues = provider.issues()
    prs = provider.prs()
    standup = provider.standup()
    ooo = provider.ooo()
    status = provider.status()
    team = provider.team()
    sprint_health = provider.sprint_health()
"""

import random
from datetime import datetime, timedelta, date


def _this_week_bounds() -> tuple[date, date]:
    """Return (monday, friday) for the current ISO week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday


def _format_iso(d: date) -> str:
    return d.isoformat()


def _format_dt(d: date, hour: int = 9, minute: int = 0) -> str:
    """Return an ISO datetime string for a given date (e.g. '2026-05-22T09:00:00')."""
    return datetime(d.year, d.month, d.day, hour, minute).isoformat()


class DemoProvider:
    """Provides mock demo data for all Axeng integrations.

    Every method returns data in the same shape as the real tool so the
    rest of the system works transparently in demo/showcase mode.
    """

    def issues(self) -> dict:
        """Return 5 mock Linear issues across different states.

        Matches the output shape of tools.linear_tool.linear_issues().
        """
        monday, friday = _this_week_bounds()
        tuesday = monday + timedelta(days=1)
        wednesday = monday + timedelta(days=2)
        yesterday = date.today() - timedelta(days=1)

        raw_issues = [
            {
                "identifier": "MAI-42",
                "title": "Implement user authentication flow",
                "state": {"name": "In Progress", "type": "started"},
                "priority": 1,
                "assignee": {"name": "Alice", "email": "alice@example.com"},
                "dueDate": _format_iso(friday),
                "labels": {"nodes": [{"name": "backend"}, {"name": "auth"}]},
                "createdAt": _format_dt(monday, 10, 30),
                "updatedAt": _format_dt(yesterday, 14, 15),
                "url": "https://linear.app/example/issue/MAI-42",
                "team": {"key": "MAI", "name": "Main"},
            },
            {
                "identifier": "MAI-43",
                "title": "Design dashboard home page",
                "state": {"name": "Todo", "type": "unstarted"},
                "priority": 2,
                "assignee": {"name": "Bob", "email": "bob@example.com"},
                "dueDate": _format_iso(friday),
                "labels": {"nodes": [{"name": "frontend"}, {"name": "design"}]},
                "createdAt": _format_dt(tuesday, 9, 0),
                "updatedAt": _format_dt(tuesday, 9, 0),
                "url": "https://linear.app/example/issue/MAI-43",
                "team": {"key": "MAI", "name": "Main"},
            },
            {
                "identifier": "MAI-38",
                "title": "Add rate limiting to API gateway",
                "state": {"name": "Done", "type": "completed"},
                "priority": 1,
                "assignee": {"name": "Carol", "email": "carol@example.com"},
                "dueDate": _format_iso(wednesday),
                "labels": {"nodes": [{"name": "backend"}, {"name": "security"}]},
                "createdAt": _format_dt(monday - timedelta(days=5), 11, 0),
                "updatedAt": _format_dt(wednesday, 16, 45),
                "url": "https://linear.app/example/issue/MAI-38",
                "team": {"key": "MAI", "name": "Main"},
            },
            {
                "identifier": "MAI-44",
                "title": "Write E2E tests for payment flow",
                "state": {"name": "Todo", "type": "unstarted"},
                "priority": 3,
                "assignee": None,
                "dueDate": None,
                "labels": {"nodes": [{"name": "testing"}, {"name": "payments"}]},
                "createdAt": _format_dt(wednesday, 8, 30),
                "updatedAt": _format_dt(wednesday, 8, 30),
                "url": "https://linear.app/example/issue/MAI-44",
                "team": {"key": "MAI", "name": "Main"},
            },
            {
                "identifier": "MAI-39",
                "title": "Update deployment pipeline docs",
                "state": {"name": "Backlog", "type": "backlog"},
                "priority": 4,
                "assignee": {"name": "Dave", "email": "dave@example.com"},
                "dueDate": _format_iso(friday + timedelta(days=7)),
                "labels": {"nodes": [{"name": "docs"}, {"name": "devops"}]},
                "createdAt": _format_dt(monday - timedelta(days=12), 14, 0),
                "updatedAt": _format_dt(monday - timedelta(days=3), 10, 0),
                "url": "https://linear.app/example/issue/MAI-39",
                "team": {"key": "MAI", "name": "Main"},
            },
        ]

        by_type = {
            "backlog": [i for i in raw_issues if i["state"]["type"] == "backlog"],
            "unstarted": [i for i in raw_issues if i["state"]["type"] == "unstarted"],
            "started": [i for i in raw_issues if i["state"]["type"] == "started"],
            "completed": [i for i in raw_issues if i["state"]["type"] == "completed"],
            "canceled": [],
            "other": [],
        }

        return {
            "tool": "linear_issues",
            "state": "open",
            "total": len(raw_issues),
            "by_state": {
                "Backlog": [
                    i["identifier"] + " — " + i["title"] for i in by_type["backlog"]
                ],
                "Todo (unstarted)": [
                    i["identifier"] + " — " + i["title"] for i in by_type["unstarted"]
                ],
                "In Progress (started)": [
                    i["identifier"] + " — " + i["title"] for i in by_type["started"]
                ],
                "Done (completed)": [
                    i["identifier"] + " — " + i["title"] for i in by_type["completed"]
                ],
                "Canceled": [],
            },
            "raw": raw_issues,
        }

    def prs(self) -> dict:
        """Return 3 mock GitHub PRs, including one stale PR.

        Matches the output shape of tools.github_activity.github_pr_health().
        """
        now = datetime.now()
        today = now.date()
        monday, friday = _this_week_bounds()
        three_days_ago = today - timedelta(days=3)
        five_days_ago = today - timedelta(days=5)

        open_prs = [
            {
                "number": 142,
                "title": "feat: add user preferences API endpoint",
                "repo": "org/api-service",
                "url": "https://github.com/org/api-service/pull/142",
                "author": "alice-dev",
                "created_at": _format_dt(monday, 11, 30),
                "updated_at": _format_dt(today, 8, 15),
                "draft": False,
                "mergeable": True,
                "mergeable_state": "clean",
                "age_days": 0,
                "created_days_ago": (today - monday).days,
                "review_count": 2,
                "reviewers": ["bob-dev", "carol-dev"],
                "reviewers_needed": [],
                "review_status": "approved",
            },
            {
                "number": 139,
                "title": "fix: handle null pointer in order serializer",
                "repo": "org/api-service",
                "url": "https://github.com/org/api-service/pull/139",
                "author": "bob-dev",
                "created_at": _format_dt(monday - timedelta(days=2), 15, 0),
                "updated_at": _format_dt(three_days_ago, 9, 45),
                "draft": False,
                "mergeable": True,
                "mergeable_state": "clean",
                "age_days": 3,
                "created_days_ago": (today - (monday - timedelta(days=2))).days,
                "review_count": 1,
                "reviewers": ["alice-dev"],
                "reviewers_needed": ["dave-dev"],
                "review_status": "changes_requested",
            },
            {
                "number": 135,
                "title": "refactor: extract payment processing module",
                "repo": "org/payments",
                "url": "https://github.com/org/payments/pull/135",
                "author": "carol-dev",
                "created_at": _format_dt(five_days_ago, 10, 0),
                "updated_at": _format_dt(five_days_ago, 10, 0),
                "draft": False,
                "mergeable": None,
                "mergeable_state": "unknown",
                "age_days": 5,
                "created_days_ago": (today - five_days_ago).days,
                "review_count": 0,
                "reviewers": [],
                "reviewers_needed": ["alice-dev", "bob-dev"],
                "review_status": "pending",
            },
        ]

        # PR 135 is stale (age_days >= 3 AND no draft)
        stale_prs = [pr for pr in open_prs if not pr["draft"] and pr["age_days"] >= 3]

        needs_review = [
            pr for pr in open_prs
            if not pr["draft"] and pr["review_status"] == "pending" and pr["review_count"] == 0
        ]
        approved_prs = [
            pr for pr in open_prs if pr["review_status"] == "approved"
        ]
        changes_requested = [
            pr for pr in open_prs if pr["review_status"] == "changes_requested"
        ]

        total_open = len([pr for pr in open_prs if not pr["draft"]])
        avg_age = sum(pr["age_days"] for pr in open_prs) / len(open_prs) if open_prs else 0

        insights = [
            {
                "level": "info",
                "category": "stale_prs",
                "message": f"{len(stale_prs)} PRs waiting >3 days",
                "action": "Check if reviewers are assigned",
            },
            {
                "level": "warning",
                "category": "review_bottleneck",
                "message": f"{len(needs_review)} PRs have no reviews yet",
                "action": "Assign reviewers to unreviewed PRs",
            },
        ]

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
                "review_velocity_per_day": 0.6,
            },
            "open_prs": open_prs,
            "stale_prs": stale_prs,
            "needs_review": needs_review,
            "approved_prs": approved_prs,
            "changes_requested": changes_requested,
            "insights": insights,
        }

    def standup(self) -> str:
        """Return a mock standup brief string.

        Matches the output style of standup-brief.py build_brief().
        """
        monday, friday = _this_week_bounds()
        yesterday = date.today() - timedelta(days=1)
        today_str = date.today().strftime("%-d %b %Y")
        yesterday_str = yesterday.strftime("%Y-%m-%d")

        lines = []
        lines.append(f"📋 Standup Brief · {today_str}\n")
        lines.append("✅ **What shipped yesterday**")
        lines.append(
            f"  • **org/api-service** (2 merged PRs): #142 add user preferences "
            f"API endpoint — Alice; #139 fix null pointer in order serializer — Bob"
        )
        lines.append(f"  • **org/payments** (1 merged PR): #138 update webhook signature "
                      f"— Carol")
        lines.append("  ↳ GitHub commit signal: 8 commits across monitored repos")
        lines.append(
            "\n👤 **Per developer achievements**"
        )
        lines.append(
            "  • **Alice** (2 PRs · api-service): add user preferences API endpoint"
        )
        lines.append(
            "  • **Bob** (1 PR, 3 commits · api-service, docs): fix null pointer in "
            "order serializer"
        )
        lines.append(
            "  • **Carol** (1 PR, 2 commits · payments): update webhook signature"
        )
        lines.append(
            "\n🚧 **Unassigned issues** (need owner)"
        )
        lines.append(
            "  🔴 `MAI-44` Write E2E tests for payment flow [Main]"
        )
        lines.append(
            "\n⏳ **Stale PRs** (1 waiting >48h for review)"
        )
        lines.append(
            "  • `org/payments#135` extract payment processing module — "
            "by Carol · 120h old · waiting on Alice, Bob"
        )
        lines.append("\n🌴 **Out today:** Dave (vacation)")
        lines.append("\n_Generated by Axeng · demo mode_")

        return "\n".join(lines)

    def ooo(self) -> dict:
        """Return 1-2 people on vacation with dates this week.

        Matches the output shape of tools.vacations.list_vacations().
        """
        monday, friday = _this_week_bounds()
        wednesday = monday + timedelta(days=2)
        next_monday = friday + timedelta(days=3)

        vacations = [
            {
                "name": "Dave Smith",
                "identifier": "MAI-99",
                "start": _format_iso(wednesday),
                "end": _format_iso(friday),
                "description": f"{_format_iso(wednesday)} → {_format_iso(friday)}",
                "url": "https://linear.app/example/issue/MAI-99",
                "state": "Started",
            },
            {
                "name": "Eva Chen",
                "identifier": "MAI-100",
                "start": _format_iso(next_monday),
                "end": _format_iso(next_monday + timedelta(days=4)),
                "description": (
                    f"{_format_iso(next_monday)} → "
                    f"{_format_iso(next_monday + timedelta(days=4))}"
                ),
                "url": "https://linear.app/example/issue/MAI-100",
                "state": "Todo",
            },
        ]

        summary_lines = []
        for v in vacations:
            summary_lines.append(
                f"• {v['name']}: {v['start']} to {v['end']} ({v['identifier']})"
            )

        return {
            "tool": "vacations",
            "month_filter": None,
            "total": len(vacations),
            "vacations": vacations,
            "summary": (
                f"{len(vacations)} vacation(s) found:\n" + "\n".join(summary_lines)
            ),
        }

    def status(self) -> dict:
        """Return integration status dict showing all services in demo mode.

        Each integration shows a green checkmark and "demo mode" status.
        """
        return {
            "tool": "integration_status",
            "mode": "demo",
            "timestamp": datetime.now().isoformat(),
            "integrations": {
                "linear": {
                    "status": "demo",
                    "icon": "✅",
                    "message": "Demo mode — no API key configured",
                },
                "github": {
                    "status": "demo",
                    "icon": "✅",
                    "message": "Demo mode — no GitHub token configured",
                },
                "google_calendar": {
                    "status": "demo",
                    "icon": "✅",
                    "message": "Demo mode — no Google credentials configured",
                },
                "granola": {
                    "status": "demo",
                    "icon": "✅",
                    "message": "Demo mode — no Granola API configured",
                },
                "llm_provider": {
                    "status": "demo",
                    "icon": "✅",
                    "message": "Demo mode — no LLM provider configured",
                },
            },
            "summary": "All integrations running in demo mode with mock data",
        }

    def team(self) -> dict:
        """Return mock team data with 4 members and their roles.

        Matches the output shape of tools.team_query.team_member_status().
        """
        monday, friday = _this_week_bounds()

        members = [
            {
                "name": "alice",
                "status": "active",
                "role": "Senior Backend Engineer",
                "email": "alice@example.com",
                "github": "alice-dev",
                "file": "team/equipa/alice.md",
            },
            {
                "name": "bob",
                "status": "active",
                "role": "Full-Stack Engineer",
                "email": "bob@example.com",
                "github": "bob-dev",
                "file": "team/equipa/bob.md",
            },
            {
                "name": "carol",
                "status": "active",
                "role": "Platform Engineer",
                "email": "carol@example.com",
                "github": "carol-dev",
                "file": "team/equipa/carol.md",
            },
            {
                "name": "dave",
                "status": "ooo",
                "role": "DevOps Engineer",
                "email": "dave@example.com",
                "github": "dave-dev",
                "file": "team/equipa/dave.md",
            },
        ]

        return {
            "tool": "team_member_status",
            "members": members,
            "count": len(members),
            "summary": {
                "total": len(members),
                "active": len([m for m in members if m["status"] == "active"]),
                "ooo": len([m for m in members if m["status"] == "ooo"]),
                "roles": {m["role"] for m in members},
            },
        }

    def sprint_health(self) -> dict:
        """Return mock sprint stats.

        Matches the output shape of tools.sprint_health.sprint_health().
        """
        now = datetime.now()
        monday, friday = _this_week_bounds()
        sprint_start = monday - timedelta(days=6)  # sprint started last Tue
        sprint_end = monday + timedelta(days=13)  # sprint ends next Sun + 1

        total_issues = 12
        completed_count = 4
        in_progress_count = 3
        todo_count = 5
        completion_rate = (completed_count / total_issues) * 100 if total_issues else 0

        total_points = 28
        completed_points = 10
        days_elapsed = max(1, (now.date() - sprint_start).days)
        velocity = completed_points / days_elapsed

        days_total = (sprint_end - sprint_start).days
        days_remaining = (sprint_end - now.date()).days

        time_progress = (days_elapsed / days_total * 100) if days_total > 0 else 0
        work_progress = completion_rate

        remaining_points = total_points - completed_points
        needed_velocity = remaining_points / days_remaining if days_remaining > 0 else 0
        on_track = work_progress >= time_progress - 10

        if on_track and velocity >= needed_velocity:
            prediction_status = "on_track"
            prediction_emoji = "🟢"
            prediction_message = "Sprint is on track"
        elif work_progress >= time_progress - 20:
            prediction_status = "at_risk"
            prediction_emoji = "🟡"
            prediction_message = "Sprint slightly behind"
        else:
            prediction_status = "off_track"
            prediction_emoji = "🔴"
            prediction_message = "Sprint significantly behind"

        insights = [
            {
                "type": "warning",
                "category": "high_wip",
                "message": f"{in_progress_count} issues in progress vs {completed_count} completed",
                "action": (
                    "Focus on completing existing work before starting new issues"
                ),
            },
            {
                "type": "success",
                "category": "healthy",
                "message": "Sprint is healthy and on track",
                "action": "Keep up the good work!",
            },
        ]

        burndown = [
            {
                "day": 0,
                "date": _format_iso(sprint_start),
                "ideal_remaining": total_points,
                "actual_remaining": total_points,
            },
            {
                "day": days_elapsed,
                "date": _format_iso(now.date()),
                "ideal_remaining": round(
                    total_points * (days_total - days_elapsed) / days_total
                ),
                "actual_remaining": remaining_points,
            },
            {
                "day": days_total,
                "date": _format_iso(sprint_end),
                "ideal_remaining": 0,
                "actual_remaining": 0,
            },
        ]

        return {
            "tool": "sprint_health",
            "timestamp": now.isoformat(),
            "cycle": {
                "name": f"Sprint {_format_iso(sprint_start)}",
                "number": 24,
                "starts_at": _format_dt(sprint_start, 9, 0),
                "ends_at": _format_dt(sprint_end, 18, 0),
                "progress": round(completion_rate, 1),
            },
            "metrics": {
                "total_issues": total_issues,
                "completed": completed_count,
                "in_progress": in_progress_count,
                "todo": todo_count,
                "completion_rate": round(completion_rate, 1),
                "velocity": round(velocity, 2),
                "estimated_points": total_points,
                "completed_points": completed_points,
                "days_elapsed": days_elapsed,
                "issues_by_state": {
                    "completed": [
                        {"identifier": "MAI-35", "title": "Redesign login page"},
                        {"identifier": "MAI-36", "title": "Add 2FA support"},
                        {"identifier": "MAI-37", "title": "Optimize DB queries"},
                        {"identifier": "MAI-38", "title": "Add rate limiting to API gateway"},
                    ],
                    "in_progress": [
                        {"identifier": "MAI-40", "title": "Implement caching layer"},
                        {"identifier": "MAI-41", "title": "Build notification system"},
                        {"identifier": "MAI-42", "title": "Implement user authentication flow"},
                    ],
                    "todo": [
                        {"identifier": "MAI-43", "title": "Design dashboard home page"},
                        {"identifier": "MAI-44", "title": "Write E2E tests for payment flow"},
                        {"identifier": "MAI-45", "title": "Set up CI/CD pipeline"},
                        {"identifier": "MAI-46", "title": "API documentation v2"},
                        {"identifier": "MAI-47", "title": "Performance audit"},
                    ],
                },
            },
            "prediction": {
                "status": prediction_status,
                "emoji": prediction_emoji,
                "message": prediction_message,
                "time_progress": round(time_progress, 1),
                "work_progress": round(work_progress, 1),
                "days_elapsed": days_elapsed,
                "days_remaining": days_remaining,
                "total_days": days_total,
                "current_velocity": round(velocity, 2),
                "needed_velocity": round(needed_velocity, 2),
                "on_track": on_track,
            },
            "insights": insights,
            "burndown": burndown,
        }