---
name: team-sync-obsidian
description: Use when Axeng needs to sync, query, repair, or explain Obsidian-backed team memory built from GitHub, Calendar, Email, and Linear context.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [obsidian, team-sync, memory, vault, notes]
    related_skills: [weekly-team-report, calendar-meeting-prep]
---

# Team Sync + Obsidian

## Overview

Obsidian is Axeng's durable team memory. Sync jobs convert raw operational signals into Markdown profiles, overview notes, metrics, and searchable context. Before answering from memory, check whether the vault has fresher or more specific context.

## When to Use

- User asks about prior team/project context.
- Team sync has to be run, repaired, or inspected.
- Weekly reports or meeting prep need persistent context.
- User asks where Axeng stores team memory.

## Commands

```bash
python3 src/team_sync.py
python3 src/tools/team_query.py summary
python3 src/tools/team_query.py status
python3 src/tools/team_query.py search "keyword"
```

Vault path usually comes from `config/config.yaml` or `OBSIDIAN_VAULT_PATH`.

## Data Flow

```text
GitHub / Calendar / Email / Linear
        ↓
team_sync.py
        ↓
Obsidian vault Markdown + metrics JSON
        ↓
team_query.py / orchestrator / reports
```

## Query Strategy

1. Search for exact project/person names first.
2. Check team overview and metrics.
3. Check person profile notes.
4. Only then summarize or recommend action.

## Common Pitfalls

1. **Answering from stale memory.** Include the last sync time when relevant.
2. **Vault path confusion.** Use configured vault path, not hardcoded assumptions.
3. **iCloud/TCC issues.** macOS may block terminal access to protected iCloud folders.
4. **Raw dump summaries.** Convert vault content into decisions and next actions.

## Verification Checklist

- [ ] Vault path resolved.
- [ ] Sync completed or last sync timestamp reported.
- [ ] Queried notes match requested person/project.
- [ ] Summary distinguishes facts from recommendations.
