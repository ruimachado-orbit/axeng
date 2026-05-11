#!/usr/bin/env python3
"""
Axeng — Granola Personal API Tool

Lists Granola notes, fetches note details and transcripts, lists folders,
and exports recent notes as Markdown. Credentials are read from environment,
./.env, ~/.axeng/.env, or ~/.hermes/.env. API keys are never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

API_BASE = "https://public-api.granola.ai/v1"
TOOL_NAME = "granola"


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            values[key.strip()] = value
    except OSError:
        pass
    return values


def load_env() -> dict[str, str]:
    """Load env vars from process, Axeng env files, and Hermes env files."""
    env = dict(os.environ)
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
        Path.home() / ".axeng" / ".env",
        Path.home() / ".hermes" / ".env",
    ]
    for path in candidates:
        for key, value in _parse_env_file(path).items():
            env.setdefault(key, value)
    return env


def api_key() -> str:
    return load_env().get("GRANOLA_API_KEY", "").strip()


def request_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    key = api_key()
    if not key:
        return {"ok": False, "tool": TOOL_NAME, "error": "MISSING_GRANOLA_API_KEY"}

    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    url = f"{API_BASE}{path}"
    if query:
        url = f"{url}?{query}"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "axeng-granola-tool/1.0",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body else {}
            if isinstance(data, dict):
                data.setdefault("ok", True)
                return data
            return {"ok": True, "data": data}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:1000]
        return {"ok": False, "tool": TOOL_NAME, "error": f"HTTP_{e.code}", "detail": detail}
    except Exception as e:
        return {"ok": False, "tool": TOOL_NAME, "error": type(e).__name__, "detail": str(e)}


def _notes_array(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("notes", "items", "data", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []


def list_notes(limit: int = 20, days: int | None = None, folder_id: str | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit}
    if folder_id:
        params["folder_id"] = folder_id
    if days:
        after = datetime.now(timezone.utc) - timedelta(days=days)
        params["updated_after"] = after.isoformat().replace("+00:00", "Z")

    payload = request_json("/notes", params)
    notes = _notes_array(payload) if payload.get("ok") else []
    return {
        "ok": payload.get("ok", False),
        "tool": "granola_notes",
        "count": len(notes),
        "notes": notes,
        "hasMore": payload.get("hasMore") or payload.get("has_more"),
        "raw": payload if not payload.get("ok") else None,
    }


def list_folders() -> dict[str, Any]:
    payload = request_json("/folders")
    folders = []
    if payload.get("ok"):
        for key in ("folders", "items", "data", "results"):
            if isinstance(payload.get(key), list):
                folders = payload[key]
                break
    return {
        "ok": payload.get("ok", False),
        "tool": "granola_folders",
        "count": len(folders),
        "folders": folders,
        "raw": payload if not payload.get("ok") else None,
    }


def get_note(note_id: str, include_transcript: bool = False) -> dict[str, Any]:
    params = {"include": "transcript"} if include_transcript else None
    payload = request_json(f"/notes/{urllib.parse.quote(note_id)}", params)
    result = {
        "ok": payload.get("ok", False),
        "tool": "granola_note",
        "note_id": note_id,
        "note": payload if payload.get("ok") else None,
        "raw": payload if not payload.get("ok") else None,
    }
    if payload.get("ok"):
        transcript = payload.get("transcript")
        result["has_transcript"] = isinstance(transcript, list) and bool(transcript)
        result["transcript_items"] = len(transcript) if isinstance(transcript, list) else 0
    return result


def latest_note(days: int = 30, include_transcript: bool = True) -> dict[str, Any]:
    """Fetch the most recent visible note, optionally with transcript."""
    notes_result = list_notes(limit=1, days=days)
    if not notes_result.get("ok"):
        return notes_result
    notes = notes_result.get("notes", [])
    if not notes:
        return {"ok": True, "tool": "granola_latest", "count": 0, "note": None, "message": "No Granola notes found"}
    note_id = notes[0].get("id") or notes[0].get("note_id")
    if not note_id:
        return {"ok": False, "tool": "granola_latest", "error": "LATEST_NOTE_HAS_NO_ID", "note": notes[0]}
    result = get_note(str(note_id), include_transcript=include_transcript)
    result["tool"] = "granola_latest"
    return result


def _text_from_transcript(transcript: Any) -> str:
    if not isinstance(transcript, list):
        return ""
    lines: list[str] = []
    for item in transcript:
        if isinstance(item, str):
            lines.append(item)
        elif isinstance(item, dict):
            speaker = item.get("speaker") or item.get("speaker_name") or item.get("user") or "Speaker"
            text = item.get("text") or item.get("content") or item.get("utterance") or ""
            if text:
                lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def export_notes(days: int = 30, output_dir: str | None = None, limit: int = 50) -> dict[str, Any]:
    notes_result = list_notes(limit=limit, days=days)
    if not notes_result.get("ok"):
        return notes_result

    out = Path(output_dir or (Path.home() / ".axeng" / "granola"))
    out.mkdir(parents=True, exist_ok=True)
    exported = []
    for note in notes_result.get("notes", []):
        note_id = note.get("id") or note.get("note_id")
        if not note_id:
            continue
        detail = get_note(str(note_id), include_transcript=True)
        if not detail.get("ok"):
            continue
        data = detail.get("note") or {}
        title = data.get("title") or note.get("title") or f"Granola note {note_id}"
        created = data.get("createdAt") or data.get("created_at") or note.get("createdAt") or ""
        summary = data.get("summary") or data.get("summary_text") or data.get("summary_markdown") or data.get("overview") or ""
        transcript_text = _text_from_transcript(data.get("transcript"))
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in title.lower()).strip("-")[:80] or str(note_id)
        path = out / f"{safe}-{note_id}.md"
        path.write_text(
            f"# {title}\n\n"
            f"- Granola ID: `{note_id}`\n"
            f"- Created: {created}\n"
            f"- URL: {data.get('url') or data.get('shareUrl') or note.get('url') or ''}\n\n"
            f"## Summary\n\n{summary}\n\n"
            f"## Transcript\n\n{transcript_text or '_No transcript returned by Granola API._'}\n",
            encoding="utf-8",
        )
        exported.append(str(path))

    return {"ok": True, "tool": "granola_export", "count": len(exported), "files": exported}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Granola Personal API helper for Axeng")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="Check API key and API access")
    sub.add_parser("folders", help="List Granola folders")

    p_notes = sub.add_parser("notes", help="List notes")
    p_notes.add_argument("--limit", type=int, default=20)
    p_notes.add_argument("--days", type=int)
    p_notes.add_argument("--folder-id")

    p_note = sub.add_parser("note", help="Fetch a note by ID")
    p_note.add_argument("note_id")
    p_note.add_argument("--transcript", action="store_true")

    p_latest = sub.add_parser("latest", help="Fetch the latest visible note")
    p_latest.add_argument("--days", type=int, default=30)
    p_latest.add_argument("--transcript", action="store_true")

    p_export = sub.add_parser("export", help="Export recent notes to Markdown")
    p_export.add_argument("--days", type=int, default=30)
    p_export.add_argument("--limit", type=int, default=50)
    p_export.add_argument("--output-dir")

    args = parser.parse_args(argv)
    if args.command == "check":
        result = list_notes(limit=1)
        result = {"ok": result.get("ok", False), "tool": "granola_check", "notes_seen": result.get("count", 0), "error": (result.get("raw") or {}).get("error")}
    elif args.command == "folders":
        result = list_folders()
    elif args.command == "notes":
        result = list_notes(limit=args.limit, days=args.days, folder_id=args.folder_id)
    elif args.command == "note":
        result = get_note(args.note_id, include_transcript=args.transcript)
    elif args.command == "latest":
        result = latest_note(days=args.days, include_transcript=args.transcript)
    elif args.command == "export":
        result = export_notes(days=args.days, limit=args.limit, output_dir=args.output_dir)
    else:
        parser.print_help(sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
