#!/usr/bin/env python3
"""
Google Workspace API Client
Handles authentication and API calls for Calendar and Gmail.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes for Calendar and Gmail access
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly'
]

# Get paths from environment or use defaults
CLIENT_SECRET_PATH = Path(os.getenv('GOOGLE_CLIENT_SECRET', '~/.hermes/google_client_secret.json')).expanduser()
TOKEN_PATH = Path(os.getenv('GOOGLE_TOKEN_PATH', '~/.hermes/google_token.json')).expanduser()


def get_credentials():
    """Get valid user credentials from storage or run OAuth flow."""
    creds = None

    # Check if token file exists
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...", file=sys.stderr)
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_PATH.exists():
                print(f"ERROR: Client secret file not found at {CLIENT_SECRET_PATH}", file=sys.stderr)
                print("Please download OAuth credentials from Google Cloud Console", file=sys.stderr)
                sys.exit(1)

            print("Starting OAuth flow...", file=sys.stderr)
            print("A browser window will open. Please authorize the application.", file=sys.stderr)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

            print(f"Authentication successful! Token saved to {TOKEN_PATH}", file=sys.stderr)

        # Save credentials for next run
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def list_calendar_events(start_time=None, end_time=None, max_results=100):
    """List calendar events within time range."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    # Default to next 7 days if no time range specified
    if not start_time:
        start_time = datetime.utcnow().isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time,
        timeMax=end_time,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Format events
    formatted_events = []
    for event in events:
        formatted_events.append({
            'id': event.get('id'),
            'summary': event.get('summary', 'No title'),
            'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
            'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
            'attendees': [att.get('email') for att in event.get('attendees', [])],
            'location': event.get('location', ''),
            'description': event.get('description', '')
        })

    return formatted_events


def list_gmail_messages(max_results=10, query=''):
    """List Gmail messages matching query."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me',
        maxResults=max_results,
        q=query
    ).execute()

    messages = results.get('messages', [])

    # Get full message details
    detailed_messages = []
    for msg in messages:
        message = service.users().messages().get(userId='me', id=msg['id']).execute()

        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}

        detailed_messages.append({
            'id': message['id'],
            'threadId': message['threadId'],
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'date': headers.get('Date', ''),
            'snippet': message.get('snippet', '')
        })

    return detailed_messages


def create_ooo_event(name: str, start_date: str, end_date: str, note: str = "") -> dict:
    """
    Create an Out-of-Office (OOO) event on Google Calendar.

    Args:
        name: Person's name (used in event title)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (exclusive — last day of vacation)
        note: Optional note (appended to description)

    Returns:
        dict with event id and url
    """
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    # Build event title
    title = f"OOO — {name}"

    # Build description
    description = f"Out of office: {name}"
    if note:
        description += f"\n\n{note}"

    # Google Calendar OOO = special "outOfOffice" transparency or all-day event
    # We create an all-day "focusTime" event marked as OOO, or use the
    # simpler approach: all-day "busy" event on primary calendar
    # Best approach: create all-day event with transparency='transparent'
    # (shows as OOO when Autoocado is enabled, or just blocks calendar)
    event = {
        'summary': title,
        'description': description,
        'start': {
            'date': start_date,
        },
        'end': {
            # 'date' is exclusive in all-day events, so add 1 day for full coverage
            'date': add_one_day(end_date),
        },
        'visibility': 'public',
        'colorId': '11',  # Light yellow — visually distinct for OOO
    }

    created = service.events().insert(
        calendarId='primary',
        body=event,
        sendNotifications=False,
    ).execute()

    return {
        'id': created.get('id'),
        'url': created.get('htmlLink'),
        'summary': created.get('summary'),
        'start': created.get('start', {}).get('date'),
        'end': created.get('end', {}).get('date'),
    }


def add_one_day(date_str: str) -> str:
    """Add one day to a YYYY-MM-DD date string."""
    from datetime import datetime, timedelta
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return (d + timedelta(days=1)).strftime("%Y-%m-%d")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: google_api.py <service> <command> [options]", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  google_api.py calendar list --start 2026-05-01T00:00:00Z --end 2026-05-08T00:00:00Z", file=sys.stderr)
        print("  google_api.py gmail list --max 20 --query 'is:unread'", file=sys.stderr)
        print("  google_api.py auth test  # Test authentication", file=sys.stderr)
        sys.exit(1)

    service = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'list'

    try:
        if service == 'auth' and command == 'test':
            # Just test authentication
            creds = get_credentials()
            print(json.dumps({"status": "authenticated", "token_path": str(TOKEN_PATH)}))

        elif service == 'calendar':
            # Parse arguments
            start = None
            end = None
            max_results = 100

            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == '--start' and i + 1 < len(sys.argv):
                    start = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--end' and i + 1 < len(sys.argv):
                    end = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--max' and i + 1 < len(sys.argv):
                    max_results = int(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1

            events = list_calendar_events(start, end, max_results)
            print(json.dumps(events, indent=2))

        elif service == 'gmail':
            # Parse arguments
            max_results = 10
            query = ''

            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == '--max' and i + 1 < len(sys.argv):
                    max_results = int(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == '--query' and i + 1 < len(sys.argv):
                    query = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            messages = list_gmail_messages(max_results, query)
            print(json.dumps(messages, indent=2))

        else:
            print(f"Unknown service: {service}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
