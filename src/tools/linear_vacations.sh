#!/usr/bin/env bash
# Linear Vacations helper – works with the "Team Vacations" project and "Vacation" label.
# Creates both a Linear issue AND a Google Calendar OOO event.
# Requires: LINEAR_API_KEY (Linear), and google_token.json at ~/.hermes/secrets/ (Calendar)
# ------------------------------------------------------------
LIN_ENDPOINT="https://api.linear.app/graphql"
VAC_LABEL_ID="d170d689-0a00-40d8-946c-80cdcd41bdc4"
VAC_PROJECT_ID="8501ab78-a3b8-49b1-9506-2da8123c7809"
TEAM_ID="cf2cc333-0afe-42bd-93d9-344b07c750aa"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AXENG_ROOT="$(dirname "$SCRIPT_DIR")"
GOOGLE_CREDS="$HOME/.hermes/google_token.json"

add_vacation() {
  local name="$1" start="$2" end="$3" note="${4:-}"

  if [[ -z "$name" || -z "$start" || -z "$end" ]]; then
    echo "Usage: add_vacation <name> <start> <end> [note]" >&2
    echo "Example: add_vacation \"Pedro Ferreira\" \"2026-07-01\" \"2026-07-10\" \"Summer break\"" >&2
    return 1
  fi

  local desc="$start → $end"
  [[ -n "$note" ]] && desc+="
$note"

  # 1) Create issue in Linear
  echo ">>> Creating Linear issue..."
  local result
  result=$(python3 -c "
import json, sys, subprocess, os

query = '''mutation(\$input: IssueCreateInput!) {
  issueCreate(input: \$input) {
    success
    issue { id identifier url }
  }
}'''

variables = {
    'input': {
        'title': '''$name'''.strip(),
        'description': '''$desc'''.strip(),
        'projectId': '$VAC_PROJECT_ID',
        'labelIds': ['$VAC_LABEL_ID'],
        'teamId': '$TEAM_ID'
    }
}

body = json.dumps({'query': query, 'variables': variables})
proc = subprocess.run(
    ['curl', '-s', '-X', 'POST', '$LIN_ENDPOINT',
     '-H', 'Authorization: $LINEAR_API_KEY',
     '-H', 'Content-Type: application/json',
     '-d', body],
    capture_output=True, text=True
)
print(proc.stdout)
")

  local success identifier url
  success=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('issueCreate',{}).get('success',''))" 2>/dev/null)
  identifier=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('issueCreate',{}).get('issue',{}).get('identifier',''))" 2>/dev/null)
  url=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('issueCreate',{}).get('issue',{}).get('url',''))" 2>/dev/null)

  if [[ "$success" != "True" && "$success" != "true" ]]; then
    echo "Error creating Linear issue:" >&2
    echo "$result" | python3 -m json.tool >&2
    return 1
  fi
  echo "  Linear: $identifier → $url"

  # 2) Create OOO event in Google Calendar (if credentials exist)
  if [[ -f "$GOOGLE_CREDS" ]]; then
    echo ">>> Creating Google Calendar OOO event..."
    local gcal_result
    gcal_result=$(python3 -c "
import sys
sys.path.insert(0, '$AXENG_ROOT')
from tools.google_api import create_ooo_event
result = create_ooo_event('''$name'''.strip(), '''$start'''.strip(), '''$end'''.strip(), '''$note'''.strip())
import json
print(json.dumps(result))
" 2>&1)
    if echo "$gcal_result" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('id') else 1)" 2>/dev/null; then
      local gcal_url gcal_id
      gcal_url=$(echo "$gcal_result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url',''))" 2>/dev/null)
      gcal_id=$(echo "$gcal_result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
      echo "  Calendar: OOO event created (ID: $gcal_id)"
    else
      echo "  Warning: Google Calendar OOO failed — Linear issue was created ($identifier)"
      echo "  Error: $gcal_result" >&2
    fi
  else
    echo "  Skipped: No Google Calendar credentials (\$GOOGLE_CREDS not found)"
  fi

  echo ""
  echo "Done — vacation created for $name ($start → $end)"
}

update_vacation() {
  local issue_id="$1" start="$2" end="$3" note="${4:-}"
  local desc="$start → $end"
  [[ -n "$note" ]] && desc+="
$note"
  python3 -c "
import json, subprocess

query = '''mutation(\$id: String!, \$input: IssueUpdateInput!) {
  issueUpdate(id: \$id, input: \$input) {
    success
    issue { id identifier }
  }
}'''

variables = {'id': '$issue_id', 'input': {'description': '''$desc'''.strip()}}
body = json.dumps({'query': query, 'variables': variables})
proc = subprocess.run(
    ['curl', '-s', '-X', 'POST', '$LIN_ENDPOINT',
     '-H', 'Authorization: $LINEAR_API_KEY',
     '-H', 'Content-Type: application/json',
     '-d', body],
    capture_output=True, text=True
)
print(proc.stdout)
" | python3 -m json.tool
}

delete_vacation() {
  local issue_id="$1"
  python3 -c "
import json, subprocess

query = '''mutation(\$id: String!) { issueDelete(id: \$id) { success } }'''
variables = {'id': '$issue_id'}
body = json.dumps({'query': query, 'variables': variables})
proc = subprocess.run(
    ['curl', '-s', '-X', 'POST', '$LIN_ENDPOINT',
     '-H', 'Authorization: $LINEAR_API_KEY',
     '-H', 'Content-Type: application/json',
     '-d', body],
    capture_output=True, text=True
)
print(proc.stdout)
" | python3 -m json.tool
}

list_vacations() {
  python3 -c "
import json, subprocess

query = '{ issues(filter: { project: { id: { eq: \"$VAC_PROJECT_ID\" } } }, first: 200) { nodes { id identifier title description url } } }'
body = json.dumps({'query': query})
proc = subprocess.run(
    ['curl', '-s', '-X', 'POST', '$LIN_ENDPOINT',
     '-H', 'Authorization: $LINEAR_API_KEY',
     '-H', 'Content-Type: application/json',
     '-d', body],
    capture_output=True, text=True
)
print(proc.stdout)
" | python3 -m json.tool
}

# Example usage (uncomment to test):
# source src/tools/linear_vacations.sh
# add_vacation "Pedro Ferreira" "2026-07-01" "2026-07-10" "Family trip"
# list_vacations
