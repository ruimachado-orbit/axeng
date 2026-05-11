---
name: github-team-intelligence
description: Use when Axeng needs to analyze GitHub repositories, PRs, reviews, contributors, stale work, quiet repos, or engineering activity signals.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [github, prs, reviews, risk, team-intel]
    related_skills: [weekly-team-report]
---

# GitHub Team Intelligence

## Overview

GitHub activity is an input to engineering judgment, not the judgment itself. Use it to find shipped work, review bottlenecks, stale PRs, quiet repositories, ownership gaps, and team contribution patterns.

## When to Use

- User asks what shipped, who contributed, or which PRs need attention.
- Weekly reports, standups, sprint health, or risk radar need repository signals.
- User asks about stale PRs, missing reviews, quiet repos, or merge risk.
- Project-to-repo mapping needs verification.

## Tools

```bash
python3 src/tools/github_activity.py
python3 src/risk-radar.py
python3 src/team_sync.py
```

Use GitHub CLI directly when deeper inspection is needed:

```bash
gh pr list --repo ORG/REPO --state open
gh pr view PR_NUMBER --repo ORG/REPO --json title,author,reviewDecision,statusCheckRollup,updatedAt,url
gh repo view ORG/REPO --json pushedAt,defaultBranchRef
```

## Analysis Heuristics

- **PR waiting >48h:** likely review bottleneck.
- **Many PRs by one person:** check overload or hidden ownership concentration.
- **Quiet repo >10 days:** risk if project is supposed to be active.
- **Repeated failed checks:** quality or CI reliability risk.
- **Large long-lived PR:** integration risk; recommend slicing.

## Response Shape

```text
🐙 GitHub signal
• Shipped: merged PRs / notable commits
• Waiting: PRs needing review or CI
• Risks: stale, failed, quiet, orphaned
• Owners: who should act
• Recommendation: next review/merge/unblock step
```

## Common Pitfalls

1. **Commit count worship.** Use impact, project relevance, and unblocking value.
2. **Bot activity.** Exclude bots and ex-members from human contribution summaries.
3. **Repo mapping drift.** Check `config/config.yaml` project mappings before attributing work to projects.
4. **Private repo errors.** Auth or org access issues can look like no activity; verify with `gh auth status`.

## Verification Checklist

- [ ] Data came from GitHub or cached sync with timestamp.
- [ ] PR URLs/numbers are included for actionable items.
- [ ] Bot/ex-member activity excluded where appropriate.
- [ ] Recommendations name owners and next actions.
