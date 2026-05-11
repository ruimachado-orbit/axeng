---
name: weekly-team-report
description: Use when Axeng needs to generate, validate, explain, send, or troubleshoot the weekly engineering team report and its Linear/email outputs.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [weekly-report, engineering-management, linear, github, email]
    related_skills: [linear-operations, github-team-intelligence, team-sync-obsidian]
---

# Weekly Team Report

## Overview

The weekly team report turns GitHub activity, Linear project status, roadmap progress, and team contributions into an executive-grade engineering digest. It is not a raw data dump: it should tell Rui what moved, what is stuck, who needs help, and what decisions are needed.

## When to Use

- Generate or test the Friday weekly report.
- Explain MVP podium, roadmap analysis, or project cards.
- Troubleshoot report generation, email delivery, or Linear project updates.
- Adjust report recipients, schedule, output directory, or sections.

## Commands

Typical commands vary by deployment, but start here:

```bash
python3 src/team_sync.py
python3 src/sprint-health.py
python3 src/risk-radar.py
python3 src/standup-brief.py
```

If a dedicated weekly report script exists in the deployment, run it from the same environment that has GitHub, Linear, Gmail, and Obsidian credentials.

## Report Quality Bar

A good weekly report contains:

- **Executive summary:** what changed this week and why it matters.
- **Project status:** each active project, owner, repo activity, Linear state.
- **MVP/contribution signal:** high-signal recognition, not vanity metrics.
- **Risks/blockers:** stale PRs, quiet repos, overloaded owners, orphaned work.
- **Next actions:** named owner + concrete follow-up.

## Verification Workflow

1. Run sync first so the report is not built from stale vault data.
2. Generate the report locally.
3. Inspect the HTML/Markdown artifact.
4. Confirm no ex-members/bots are highlighted as contributors.
5. Confirm Linear project mappings are correct.
6. If sending email or posting Linear updates, do a Rui-only test first when possible.

## Recipient Safety

- Test runs should go only to the requester unless explicitly asked otherwise.
- Full-team reports should run on the agreed schedule only.
- Never email raw secrets, private keys, or internal debug payloads.

## Common Pitfalls

1. **Stale sync.** Run team sync before reports.
2. **Bot noise.** Exclude dependabot, GitHub Actions, Renovate, and ex-members.
3. **Misleading MVP.** Favor impact and unblockers over raw commit counts.
4. **Cron vs LaunchAgent.** For deterministic scheduled scripts on macOS, prefer LaunchAgent over LLM cron paths.

## Verification Checklist

- [ ] Report generated without exceptions.
- [ ] Output artifact exists and is readable.
- [ ] GitHub + Linear sections match source data.
- [ ] Risk and next-action sections are specific.
- [ ] Delivery target is correct before send/post.
