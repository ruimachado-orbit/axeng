#!/usr/bin/env python3
"""
Vacation/PTO Tool - Query Linear for team vacations
Searches the Team Vacations project for who is OOO
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent for config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import linear_query from linear_tool
from tools.linear_tool import linear_query, load_env


# Vacation project ID (from linear_vacations.sh)
VACATION_PROJECT_ID = "VACATION_PROJECT_ID_PLACEHOLDER"


def list_vacations(month: str = None) -> dict:
    """
    List vacations from Linear vacation project.

    Args:
        month: Optional month filter like "may", "2026-05", or "may 2026"

    Returns:
        dict with vacation list and summary
    """
    # Query all vacations from the project
    query = """
    query($projectId: String!) {
      issues(
        filter: { project: { id: { eq: $projectId } } }
        first: 200
      ) {
        nodes {
          id
          identifier
          title
          description
          url
          state { name type }
          createdAt
          updatedAt
        }
      }
    }
    """

    result = linear_query(query, {"projectId": VACATION_PROJECT_ID})

    if "errors" in result:
        return {
            "tool": "vacations",
            "error": result["errors"][0]["message"],
            "vacations": []
        }

    issues = result.get("data", {}).get("issues", {}).get("nodes", [])

    # Parse vacation dates from descriptions (format: "2026-05-12 → 2026-05-19")
    vacations = []
    for issue in issues:
        desc = issue.get("description", "")
        title = issue.get("title", "")

        # Extract dates from description
        dates = extract_dates(desc)

        vac = {
            "name": title,
            "identifier": issue.get("identifier"),
            "start": dates.get("start"),
            "end": dates.get("end"),
            "description": desc,
            "url": issue.get("url"),
            "state": issue.get("state", {}).get("name")
        }

        # Filter by month if specified
        if month and dates.get("start"):
            if not matches_month(dates["start"], month):
                continue

        vacations.append(vac)

    # Sort by start date
    vacations.sort(key=lambda x: x.get("start") or "9999")

    return {
        "tool": "vacations",
        "month_filter": month,
        "total": len(vacations),
        "vacations": vacations,
        "summary": format_summary(vacations, month)
    }


def extract_dates(text: str) -> dict:
    """Extract start and end dates from vacation description."""
    import re

    # Match format: "2026-05-12 → 2026-05-19"
    match = re.search(r'(\d{4}-\d{2}-\d{2})\s*[→->]\s*(\d{4}-\d{2}-\d{2})', text)
    if match:
        return {"start": match.group(1), "end": match.group(2)}

    # Match single date
    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if match:
        return {"start": match.group(1), "end": match.group(1)}

    return {}


def matches_month(date_str: str, month_filter: str) -> bool:
    """Check if date matches month filter."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        month_lower = month_filter.lower()

        # Parse month filter
        if "-" in month_filter:  # Format: "2026-05"
            filter_date = datetime.strptime(month_filter, "%Y-%m")
            return date.year == filter_date.year and date.month == filter_date.month

        # Month name
        months = {
            "january": 1, "jan": 1,
            "february": 2, "feb": 2,
            "march": 3, "mar": 3,
            "april": 4, "apr": 4,
            "may": 5,
            "june": 6, "jun": 6,
            "july": 7, "jul": 7,
            "august": 8, "aug": 8,
            "september": 9, "sep": 9,
            "october": 10, "oct": 10,
            "november": 11, "nov": 11,
            "december": 12, "dec": 12,
        }

        for name, num in months.items():
            if name in month_lower:
                # Extract year if present
                year_match = re.search(r'20\d{2}', month_filter)
                year = int(year_match.group()) if year_match else datetime.now().year

                return date.year == year and date.month == num

        return True
    except:
        return True


def format_summary(vacations: list, month: str = None) -> str:
    """Format vacation summary."""
    if not vacations:
        period = f" in {month}" if month else ""
        return f"No vacations found{period}."

    lines = []
    for v in vacations:
        date_range = f"{v['start']} to {v['end']}" if v.get('start') and v.get('end') else "dates TBD"
        lines.append(f"• {v['name']}: {date_range} ({v['identifier']})")

    period = f" in {month}" if month else ""
    return f"{len(vacations)} vacation(s) found{period}:\n" + "\n".join(lines)


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Query Linear vacations/PTO")
    parser.add_argument("action", choices=["list"], default="list", nargs="?",
                       help="Action to perform")
    parser.add_argument("--month", help="Filter by month (e.g., 'may', '2026-05', 'may 2026')")

    args = parser.parse_args()

    if args.action == "list":
        result = list_vacations(args.month)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
