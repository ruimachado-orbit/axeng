#!/usr/bin/env bash
# Linear Vacations helper – works with the "Team Vacations" project and "Vacation" label.
# Requires the environment variable LINEAR_API_KEY to be set.
# ------------------------------------------------------------
LIN_ENDPOINT="https://api.linear.app/graphql"
VAC_LABEL_ID="${VAC_LABEL_ID:-VAC_LABEL_ID_PLACEHOLDER}"
VAC_PROJECT_ID="VACATION_PROJECT_ID_PLACEHOLDER"
TEAM_ID="${TEAM_ID:-TEAM_ID_PLACEHOLDER}"

add_vacation() {
  local name=$1 start=$2 end=$3 note=${4:-}
  local desc="$start → $end"
  [[ -n "$note" ]] && desc+="\n\n$note"
  curl -s -X POST "$LIN_ENDPOINT" \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\n      \"query\":\"mutation(\$input: IssueCreateInput!){issueCreate(input:\$input){success issue{id identifier url}}}\",\n      \"variables\":{\n        \"input\":{\n          \"title\":\"$name\",\n          \"description\":\"$desc\",\n          \"projectId\":\"$VAC_PROJECT_ID\",\n          \"labelIds\":[\"$VAC_LABEL_ID\"],\n          \"teamId\":\"$TEAM_ID\"\n        }\n      }\n    }" | python3 -m json.tool
}

update_vacation() {
  local issue_id=$1 start=$2 end=$3 note=${4:-}
  local desc="$start → $end"
  [[ -n "$note" ]] && desc+="\n\n$note"
  curl -s -X POST "$LIN_ENDPOINT" \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\n      \"query\":\"mutation(\$id: String!, \$input: IssueUpdateInput!){issueUpdate(id:\$id, input:\$input){success issue{id identifier}}}\",\n      \"variables\":{\n        \"id\":\"$issue_id\",\n        \"input\":{\n          \"description\":\"$desc\"\n        }\n      }\n    }" | python3 -m json.tool
}

delete_vacation() {
  local issue_id=$1
  curl -s -X POST "$LIN_ENDPOINT" \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\n      \"query\":\"mutation(\$id: String!){issueDelete(id:\$id){success}}\",\n      \"variables\":{\"id\":\"$issue_id\"}\n    }" | python3 -m json.tool
}

list_vacations() {
  curl -s -X POST "$LIN_ENDPOINT" \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\n      \"query\":\"{ issues(filter: { project: { id: { eq: \"$VAC_PROJECT_ID\" } } }, first: 200) { nodes { id identifier title description url } } }\"\n    }" | python3 -m json.tool
}

# Example usage (uncomment to test):
# add_vacation "John Doe" "2026-07-12" "2026-07-19" "Family trip"
# list_vacations
