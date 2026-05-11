---
name: offboarding
description: Use when Axeng needs to preview, execute, or audit offboarding across GitHub organizations and Linear workspace access.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [offboarding, security, github, linear, access]
    related_skills: [linear-operations, github-team-intelligence]
---

# Offboarding

## Overview

Offboarding is destructive and security-sensitive. Default to preview/dry-run, show exact scope, and require explicit confirmation before removing access. Verify the final state after execution.

## When to Use

- User asks to remove a person from GitHub orgs/repos or Linear.
- User asks to audit a person's access.
- User asks whether someone is still active in systems.

## Tool

```bash
python3 src/tools/offboarding.py <github_login> --dry-run
python3 src/tools/offboarding.py <github_login>
```

## Safety Protocol

1. **Identify the person.** Confirm GitHub login, email, and display name.
2. **Dry-run first.** Always preview removals.
3. **Report scope.** List orgs, repos/teams, Linear user/workspace impact.
4. **Confirm destructive execution.** Do not execute removal on ambiguous identity.
5. **Verify after execution.** Re-check GitHub and Linear access.

## Output Shape

```text
🛡️ Offboarding preview
• Person: name / email / github
• GitHub orgs: list
• Linear: status
• Will remove: explicit scope
• Will not touch: explicit exclusions
• Confirmation needed: yes/no
```

## Common Pitfalls

1. **Wrong identity.** Similar names/logins require confirmation.
2. **Skipping dry-run.** Never jump straight to destructive execution.
3. **Partial offboarding.** GitHub removal without Linear verification is incomplete.
4. **No audit trail.** Log what changed and when.

## Verification Checklist

- [ ] Dry-run output captured.
- [ ] Scope confirmed by requester.
- [ ] Execution completed with no unhandled errors.
- [ ] Post-check confirms removed access.
- [ ] Audit/session log written.
