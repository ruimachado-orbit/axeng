#!/usr/bin/env python3
"""
Smart Query Suggestions
Context-aware query suggestions based on time, day, and user patterns.
"""

from datetime import datetime, time as dt_time
from typing import List, Dict
import random


def get_smart_suggestions(limit: int = 3) -> List[Dict[str, str]]:
    """
    Get smart query suggestions based on current context.

    Returns:
        List of suggestions with 'query' and 'reason' keys
    """
    now = datetime.now()
    hour = now.hour
    day_of_week = now.strftime("%A")

    suggestions = []

    # Time-based suggestions
    if 7 <= hour < 10:
        # Morning routine
        suggestions.extend([
            {
                "query": "What's the standup brief?",
                "reason": "☀️ Morning - Generate daily standup"
            },
            {
                "query": "Who's out of office today?",
                "reason": "☀️ Morning - Check team availability"
            },
            {
                "query": "Show my Linear issues",
                "reason": "☀️ Morning - Review your tasks"
            }
        ])
    elif 10 <= hour < 12:
        # Mid-morning
        suggestions.extend([
            {
                "query": "Show PR health status",
                "reason": "🔍 Mid-morning - Review PR pipeline"
            },
            {
                "query": "What's blocked?",
                "reason": "🔍 Mid-morning - Check blockers"
            }
        ])
    elif 12 <= hour < 14:
        # Lunch time
        suggestions.extend([
            {
                "query": "Show PR health status",
                "reason": "🍽️ Lunch - Quick status check"
            },
            {
                "query": "What shipped this week?",
                "reason": "🍽️ Lunch - Review progress"
            }
        ])
    elif 14 <= hour < 17:
        # Afternoon
        suggestions.extend([
            {
                "query": "Show me stale PRs",
                "reason": "⏰ Afternoon - Clear review backlog"
            },
            {
                "query": "What needs my review?",
                "reason": "⏰ Afternoon - Review requests"
            }
        ])
    elif 17 <= hour < 19:
        # End of day
        suggestions.extend([
            {
                "query": "What did I ship today?",
                "reason": "🌆 End of day - Daily summary"
            },
            {
                "query": "Show tomorrow's meetings",
                "reason": "🌆 End of day - Prep for tomorrow"
            }
        ])

    # Day-specific suggestions
    if day_of_week == "Monday":
        suggestions.extend([
            {
                "query": "What happened over the weekend?",
                "reason": "📅 Monday - Weekend recap"
            },
            {
                "query": "Show sprint goals",
                "reason": "📅 Monday - Week kickoff"
            }
        ])
    elif day_of_week == "Friday":
        suggestions.extend([
            {
                "query": "Show sprint health",
                "reason": "📅 Friday - Week in review"
            },
            {
                "query": "What shipped this week?",
                "reason": "📅 Friday - Weekly summary"
            },
            {
                "query": "Who's on vacation next week?",
                "reason": "📅 Friday - Plan ahead"
            }
        ])

    # Meeting-related suggestions (if current hour has typical meeting times)
    if 9 <= hour < 17:
        suggestions.append({
            "query": "Prep for 1:1 with [name]",
            "reason": "📋 Before meetings - Prepare talking points"
        })

    # Always useful suggestions
    always_useful = [
        {
            "query": "Show my GitHub PRs",
            "reason": "📦 Anytime - Check your PRs"
        },
        {
            "query": "Check integration status",
            "reason": "⚙️ Anytime - Verify connections"
        },
        {
            "query": "Show team activity",
            "reason": "👥 Anytime - Team overview"
        }
    ]

    # Add some always-useful suggestions
    suggestions.extend(random.sample(always_useful, min(2, len(always_useful))))

    # Deduplicate and shuffle
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s["query"] not in seen:
            seen.add(s["query"])
            unique_suggestions.append(s)

    # Return top suggestions (prioritize time/day-specific ones)
    return unique_suggestions[:limit]


def format_suggestions_for_display(suggestions: List[Dict[str, str]]) -> str:
    """
    Format suggestions as a rich text display string.

    Args:
        suggestions: List of suggestion dicts

    Returns:
        Formatted string for terminal display
    """
    if not suggestions:
        return ""

    lines = ["[bold cyan]💡 Suggested queries:[/bold cyan]\n"]
    for i, suggestion in enumerate(suggestions, 1):
        lines.append(f"  {i}. [bold]{suggestion['query']}[/bold]")
        lines.append(f"     [dim]{suggestion['reason']}[/dim]")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test the suggestions
    suggestions = get_smart_suggestions(limit=5)
    print(format_suggestions_for_display(suggestions))
    print("\n--- JSON output ---")
    import json
    print(json.dumps(suggestions, indent=2))
