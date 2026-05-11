---
name: linear-operations
description: Use when Axeng needs to read, create, update, label, assign, or report on Linear issues, projects, vacations, CRM leads, and team operations.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [linear, issues, projects, crm, vacations, operations]
    related_skills: [weekly-team-report]
---

# Linear Operations

## Overview

Linear is Axeng's operational system of record for engineering work, CRM leads, vacations, blockers, and project status. Use the Linear tools before answering status questions. Treat mutations as operational changes: verify before and after, and never expose API keys.

## When to Use

- User asks for issue/project status, priorities, assignees, blockers, or roadmap state.
- User asks to create/update/label/assign Linear issues or projects.
- User asks about vacations tracked in Linear.
- User asks for CRM lead status or lead cleanup.
- Weekly reports need Linear project summaries or project updates.

## Tools

```bash
python3 src/tools/linear_tool.py summary
python3 src/tools/linear_tool.py issues open
python3 src/tools/linear_tool.py mine
python3 src/tools/linear_tool.py blockers 7
python3 src/tools/linear_tool.py person person@example.com
python3 src/tools/linear_tool.py sync
```

Vacation helpers, when present:

```bash
source src/tools/linear_vacations.sh
list_vacations
add_vacation "Name" "YYYY-MM-DD" "YYYY-MM-DD" "note"
update_vacation ISSUE_ID "YYYY-MM-DD" "YYYY-MM-DD" "note"
delete_vacation ISSUE_ID
```

## Operating Rules

1. **Read before write.** Query the issue/project/user/label first.
2. **Use IDs for mutations.** Resolve names to IDs before update/delete.
3. **Verify after write.** Re-query the issue/project and check the fields changed.
4. **Be explicit about scope.** Mutating many issues/projects requires a summary of intended targets.
5. **Never print credentials.** `LINEAR_API_KEY` is env-only and must not appear in output.
6. **Prefer labels over title hacks.** Use labels for sources (`DRA AUGUSTA`), domains, and workflow classes.

## Status Response Shape

```text
📋 Linear status
• Scope: project/team/filter
• Total: N
• By state: Backlog / Todo / In Progress / Done
• Owners: names
• Blockers: explicit list or "none found"
• Next action: concrete recommendation
```

## Mutation Checklist

- [ ] Entity exists and exact target is known.
- [ ] Mutation is reversible or confirmed if destructive.
- [ ] API response has no errors.
- [ ] Post-write query confirms final state.
- [ ] User-facing summary includes changed identifiers and URLs.

## Common Pitfalls

1. **Bearer auth.** Linear API keys in this repo use raw `Authorization: KEY`, not `Bearer KEY`.
2. **Duplicate-looking issues.** Report duplicates before merging/deleting; do not clean up unless asked.
3. **Workspace assumptions.** Query teams/projects instead of hardcoding team names.
4. **Silent GraphQL errors.** Always inspect the `errors` field, not just HTTP status.
