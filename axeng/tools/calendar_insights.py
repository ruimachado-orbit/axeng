#!/usr/bin/env python3
"""
Team Intel — Calendar Insights Tool
Returns structured meeting data, 1:1s, team events.
Stub with graceful fallback when Google Calendar is unavailable.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get, vault_path


# Default to built-in calendar if Google API unavailable
DEFAULT_GAPI_SCRIPT = "~/.axeng/skills/productivity/google-workspace/scripts/google_api.py"


def fetch_calendar_via_gapi(days: int = 7) -> list:
    """Attempt to fetch calendar via Google API script."""
    gapi_path = Path(DEFAULT_GAPI_SCRIPT).expanduser()
    
    if not gapi_path.exists():
        return None
    
    try:
        start = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%dT23:59:59Z")
        
        result = subprocess.run(
            ["python3", str(gapi_path), "calendar", "list", "--start", start, "--end", end],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    
    return None


def get_events_from_obsidian(days: int = 7) -> list:
    """Try to get calendar events from synced Obsidian files."""
    vault = vault_path()
    calendar_dir = Path(vault) / "calendar"
    
    if not calendar_dir.exists():
        return []
    
    events = []
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    for f in calendar_dir.glob("*.md"):
        try:
            content = f.read_text()
            # Simple parsing of frontmatter or event format
            # Adapt based on your Obsidian calendar sync format
            for line in content.split("\n"):
                if "dtstart:" in line.lower() or "start:" in line.lower():
                    # Extract date and create event
                    events.append({
                        "summary": f.stem,
                        "date": line.split(":")[-1].strip(),
                        "source": "obsidian"
                    })
        except Exception:
            pass
    
    return events


# ─────────────────────────────────────────────
# TOOL: calendar_insights — Meeting insights
# ─────────────────────────────────────────────

def calendar_insights(days: int = 7, meeting_type: str = "all") -> dict:
    """
    Return structured calendar insights.
    
    days: lookback window (default: 7)
    meeting_type: 'all', '1on1', 'team', 'decisions'
    """
    result = {
        "tool": "calendar_insights",
        "today": [],
        "this_week": [],
        "1on1s": [],
        "team_meetings": [],
        "decisions_meetings": [],
        "summary": {},
        "source": "fallback"
    }
    
    # Try Google API first
    events = fetch_calendar_via_gapi(days)
    
    if events is None:
        # Try Obsidian sync
        events = get_events_from_obsidian(days)
        if events:
            result["source"] = "obsidian"
        else:
            result["available"] = False
            result["message"] = "Calendar integration not configured"
            result["setup_instructions"] = "Run 'axeng configure' to set up Google Calendar integration"
            result["summary"] = {
                "today_count": 0,
                "this_week_count": 0,
                "1on1_count": 0,
                "team_meetings_count": 0,
                "decisions_pending": 0
            }
            return result
    
    today = datetime.now().date()
    week_end = today + timedelta(days=days)
    
    for event in events:
        summary = event.get("summary", "No title")
        start = event.get("start", "")
        attendees = event.get("attendees", [])
        
        try:
            if "T" in str(start):
                event_date = datetime.fromisoformat(str(start).replace("Z", "+00:00")).date()
            else:
                event_date = today
        except Exception:
            event_date = today
        
        event_data = {
            "title": summary,
            "start": start,
            "end": event.get("end", ""),
            "attendees": attendees,
            "location": event.get("location", ""),
            "id": event.get("id", "")
        }
        
        # Categorize
        if event_date == today:
            result["today"].append(event_data)
        
        if today <= event_date <= week_end:
            result["this_week"].append(event_data)
        
        # Type-specific
        lower_title = summary.lower()
        if "1:1" in lower_title or "one-on-one" in lower_title:
            result["1on1s"].append(event_data)
        elif any(kw in lower_title for kw in ["standup", "daily", "planning", "retro", "review", "sprint", "team"]):
            result["team_meetings"].append(event_data)
        elif any(kw in lower_title for kw in ["decision", "architecture", "design"]):
            result["decisions_meetings"].append(event_data)
    
    # Filter by meeting_type if not 'all'
    if meeting_type != "all":
        for key in ["today", "this_week", "1on1s", "team_meetings", "decisions_meetings"]:
            result[key] = []
    
    # Summary
    result["summary"] = {
        "today_count": len(result["today"]),
        "this_week_count": len(result["this_week"]),
        "1on1_count": len(result["1on1s"]),
        "team_meetings_count": len(result["team_meetings"]),
        "decisions_pending": len(result["decisions_meetings"])
    }
    
    return result


def get_person_meetings(person_name: str, days: int = 7) -> dict:
    """Get all meetings for a specific person."""
    events = fetch_calendar_via_gapi(days)
    
    if events is None:
        events = get_events_from_obsidian(days)
    
    person_lower = person_name.lower()
    result = {
        "tool": "get_person_meetings",
        "person": person_name,
        "1on1s": [],
        "team_meetings": [],
        "all_meetings": []
    }
    
    if not events:
        return result
    
    for event in events:
        title = event.get("summary", "").lower()
        attendees = event.get("attendees", [])
        
        is_relevant = person_lower in title or any(person_lower in str(a).lower() for a in attendees)
        
        if is_relevant:
            event_data = {
                "title": event.get("summary"),
                "start": event.get("start"),
                "attendees": attendees
            }
            result["all_meetings"].append(event_data)
            
            lower_title = event.get("summary", "").lower()
            if "1:1" in lower_title:
                result["1on1s"].append(event_data)
            else:
                result["team_meetings"].append(event_data)
    
    return result


def today_schedule() -> dict:
    """Get today's meeting schedule."""
    insights = calendar_insights(days=1)
    
    return {
        "tool": "today_schedule",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "meetings": insights.get("today", []),
        "count": len(insights.get("today", []))
    }


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "insights"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    if cmd == "insights":
        data = calendar_insights(days=days)
    elif cmd == "person":
        person = sys.argv[3] if len(sys.argv) > 3 else ""
        data = get_person_meetings(person, days=days)
    elif cmd == "today":
        data = today_schedule()
    else:
        data = {"error": f"Unknown command: {cmd}"}
    
    print(json.dumps(data, indent=2, default=str))