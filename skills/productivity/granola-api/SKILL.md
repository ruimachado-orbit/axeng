---
name: granola-api
description: Use when Axeng needs to retrieve, summarize, export, or troubleshoot Granola meeting notes, summaries, folders, and transcripts through the Granola Personal API.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [granola, meetings, transcripts, notes, productivity, axeng]
    related_skills: [google-workspace, obsidian]
---

# Granola API

## Overview

Axeng can connect to the Granola Personal API to retrieve meeting notes, summaries, folders, and transcripts. Use the built-in tool at `src/tools/granola_tool.py`; do not write ad-hoc curl snippets unless you are debugging the tool itself.

Credentials stay local. The API key is read from `GRANOLA_API_KEY` in the process environment, `.env`, `~/.axeng/.env`, or `~/.hermes/.env`. Never print or commit the key.

## When to Use

Use this skill when the user asks to:

- List recent Granola notes or folders.
- Fetch a specific Granola note by ID.
- Retrieve a transcript from a Granola note.
- Summarize meeting notes from Granola.
- Export Granola notes/transcripts to Markdown for Obsidian, reports, or follow-ups.
- Troubleshoot missing Granola notes/transcripts.

Do not use this for live meeting recording. Granola records meetings; Axeng consumes the completed note through the API.

## Setup

1. Create a Granola Personal API key:
   - Granola desktop → Settings → Connectors → API keys → Create Personal API key.
2. Store it locally:
   ```bash
   GRANOLA_API_KEY=***
   ```
3. Prefer `.env` for standalone Axeng or `~/.hermes/.env` when running integrated with Hermes.
4. Verify access:
   ```bash
   python3 src/tools/granola_tool.py check
   ```

Expected success shape:

```json
{
  "ok": true,
  "tool": "granola_check",
  "notes_seen": 1,
  "error": null
}
```

## Commands

### List recent notes

```bash
python3 src/tools/granola_tool.py notes --days 7 --limit 10
```

### List folders

```bash
python3 src/tools/granola_tool.py folders
```

### Fetch latest note with transcript

```bash
python3 src/tools/granola_tool.py latest --days 30 --transcript
```

### Fetch one note with transcript

```bash
python3 src/tools/granola_tool.py note not_xxxxxxxxxxxxxx --transcript
```

The tool calls:

```text
GET https://public-api.granola.ai/v1/notes/{note_id}?include=transcript
```

### Export notes to Markdown

```bash
python3 src/tools/granola_tool.py export --days 30
```

Default output directory:

```text
~/.axeng/granola/
```

Override it with:

```bash
python3 src/tools/granola_tool.py export --days 30 --output-dir ~/Documents/GranolaExports
```

## Orchestrator Integration

Axeng's orchestrator routes Granola-related natural-language requests to the Granola tools when the prompt contains terms such as:

- `granola`
- `transcript`, `transcription`, `transcrições`, `transcricoes`
- `meeting notes`, `call notes`, `notas da reunião`, `notas de reunião`

Default tool registry entries:

```yaml
granola_notes:
  script: granola_tool.py
  args: ["notes", "--days", "30", "--limit", "20"]
  purpose: "List recent Granola meeting notes"

granola_latest:
  script: granola_tool.py
  args: ["latest", "--days", "30", "--transcript"]
  purpose: "Fetch the latest Granola note with transcript"

granola_folders:
  script: granola_tool.py
  args: ["folders"]
  purpose: "List Granola folders"

granola_export:
  script: granola_tool.py
  args: ["export", "--days", "30"]
  purpose: "Export recent Granola notes and transcripts to Markdown"
```

## Troubleshooting

1. **`MISSING_GRANOLA_API_KEY`**
   - Set `GRANOLA_API_KEY` in `.env`, `~/.axeng/.env`, or `~/.hermes/.env`.
   - Restart the process/container if the environment is already loaded.

2. **Auth works but `notes` returns zero results**
   - New Granola keys/accounts may have no accessible notes yet.
   - Create or open a completed Granola note and retry.
   - Check folders with `python3 src/tools/granola_tool.py folders`.

3. **Transcript is empty but summary exists**
   - This can happen on short test notes or notes where Granola did not return transcript segments.
   - Retry after Granola finishes processing the meeting.
   - Test with a real/longer meeting note.

4. **Do not expose secrets**
   - Never paste the raw key into logs, reports, GitHub issues, Linear comments, or chat.
   - Redact as `[REDACTED]` when documenting.

## Verification Checklist

- [ ] `python3 src/tools/granola_tool.py check` returns `ok: true`.
- [ ] `python3 src/tools/granola_tool.py folders` returns folders or an empty valid list.
- [ ] `python3 src/tools/granola_tool.py notes --days 30 --limit 5` returns JSON without exposing the key.
- [ ] `python3 src/tools/granola_tool.py note NOTE_ID --transcript` works for a known note.
- [ ] `python3 src/tools/granola_tool.py export --days 30` writes Markdown files when notes are available.
