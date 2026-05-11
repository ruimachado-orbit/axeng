---
name: calendar-meeting-prep
description: Use when Axeng needs to prepare for meetings, 1:1s, standups, OOO planning, calendar context, or pre-read briefs.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [calendar, meetings, 1on1, pre-read, granola]
    related_skills: [granola-api, linear-operations, github-team-intelligence]
---

# Calendar Meeting Prep

## Overview

Meeting prep should reduce cognitive load before the meeting starts. Combine calendar context with Linear, GitHub, Obsidian, and Granola notes to produce a concise pre-read: purpose, current work, open threads, risks, and suggested questions.

## When to Use

- User asks for meeting prep, 1:1 prep, agenda, or calendar insights.
- A pre-meeting briefing is generated automatically.
- User asks who is OOO or what meetings are coming.
- Granola notes should inform a follow-up or next meeting.

## Tools

```bash
python3 src/tools/calendar_insights.py insights 7
python3 src/tools/linear_tool.py person person@example.com
python3 src/tools/granola_tool.py notes --days 30 --limit 10
python3 src/tools/team_query.py person "Name"
```

## Pre-read Shape

```text
🗓️ Meeting prep — <title>
• When / attendees
• Context: last relevant notes or project state
• Current work: Linear + GitHub signal
• Risks/blockers
• Suggested questions
• Decisions needed
```

## 1:1 Guidance

For 1:1s, optimize for coaching and unblockers:

- Start with their current priorities.
- Identify blocked or stale work.
- Mention recent wins.
- Bring one coaching question, not ten.
- Capture follow-ups in Linear or notes.

## Common Pitfalls

1. **Calendar-only prep.** Meeting titles are not enough; enrich with Linear/GitHub/notes.
2. **Overlong briefs.** Pre-reads should be scannable in under 60 seconds.
3. **Missing privacy boundary.** Do not expose sensitive notes to unrelated attendees.
4. **Stale Granola processing.** Recently ended meetings may not have transcript yet.

## Verification Checklist

- [ ] Calendar event and attendees are correct.
- [ ] Names mapped to team members where possible.
- [ ] Related Linear/GitHub context included.
- [ ] Questions and decisions are actionable.
