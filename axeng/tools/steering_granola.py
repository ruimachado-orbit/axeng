#!/usr/bin/env python3
"""
CEO Steering Report — Granola Transcript Intelligence
Fetches meeting notes from the last 7 days, attributes them to projects,
and extracts structured signals (decisions, blockers, commitments, risks).

Main entry:  enrich_with_granola(project_cards, week_start) -> list[ProjectCard]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.granola_tool import list_notes, get_note, _text_from_transcript
from tools.steering_schema import Evidence, TranscriptSignal

# Lazy import to avoid hard dependency when Granola is not configured
_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        from llm_gateway import call_with_fallback
        _llm = call_with_fallback
    return _llm


# ── Project attribution ──────────────────────────────────────────────────────

def _keyword_match(text: str, project_names: list[str]) -> list[str]:
    """Return project names whose name (or any word ≥5 chars) appears in text."""
    text_lower = text.lower()
    matched = []
    for name in project_names:
        # Full name match
        if name.lower() in text_lower:
            matched.append(name)
            continue
        # Partial word match (any token ≥5 chars from project name)
        for token in re.split(r"[\s\-_/]+", name):
            if len(token) >= 5 and token.lower() in text_lower:
                matched.append(name)
                break
    return matched


def _llm_attribute(title: str, content_snippet: str, project_names: list[str]) -> list[str]:
    """Ask LLM to attribute a note to projects when keyword match fails."""
    if not project_names:
        return []

    prompt = (
        f"Meeting note title: {title}\n"
        f"Content snippet: {content_snippet[:500]}\n\n"
        f"Active projects: {', '.join(project_names)}\n\n"
        "Which of the above projects does this meeting note most likely relate to?\n"
        "Return JSON only: {\"projects\": [\"name1\"], \"confidence\": \"high|medium|none\"}\n"
        "Return empty projects list if the note is not clearly related to any project."
    )
    try:
        result = _get_llm()(prompt, json_output=True, max_tokens=256)
        if result.get("ok"):
            parsed = json.loads(result["text"]) if isinstance(result["text"], str) else result["text"]
            if parsed.get("confidence") != "none":
                return parsed.get("projects", [])
    except Exception:
        pass
    return []


def _attribute_note(
    title: str, content: str, folder_name: str | None, project_names: list[str]
) -> list[str]:
    """
    Return list of project names this note belongs to.
    Strategy: keyword match in title/folder first, then full content, then LLM fallback.
    """
    # Check folder name first (most reliable signal)
    search_text = f"{folder_name or ''} {title}"
    matched = _keyword_match(search_text, project_names)
    if matched:
        return matched

    # Check note content
    matched = _keyword_match(content[:1000], project_names)
    if matched:
        return matched

    # LLM fallback
    return _llm_attribute(title, content, project_names)


# ── Transcript extraction ────────────────────────────────────────────────────

_EXTRACTION_PROMPT = """\
You are extracting executive signals from a meeting note for a CEO weekly report.

Meeting: {title}
Date: {date}
Content:
{content}

Return JSON only with this exact shape:
{{
  "decisions": [{{"text": "...", "owner": null, "deadline": null}}],
  "blockers":  [{{"text": "...", "severity": "high|medium|low"}}],
  "commitments": [{{"text": "...", "owner": "...", "due": null}}],
  "risks":     [{{"text": "..."}}],
  "confidence_tone": "positive|neutral|concerned|urgent"
}}

Rules:
- Only include items explicitly stated, not inferred from context
- Maximum 3 items per category
- If a category has nothing, return []
- confidence_tone: urgent = escalation / critical blocker mentioned; concerned = risk/delay; positive = shipped / milestone hit
"""


def _extract_signals_from_note(note_data: dict) -> dict:
    """Extract structured signals from a single note via LLM."""
    title = note_data.get("title", "Untitled")
    created = (note_data.get("createdAt") or note_data.get("created_at") or "")[:10]

    # Build content from summary + transcript
    summary = (
        note_data.get("summary")
        or note_data.get("summary_text")
        or note_data.get("summary_markdown")
        or ""
    )
    transcript_items = note_data.get("transcript", [])
    transcript_text = _text_from_transcript(transcript_items)

    # Use summary first (denser), pad with transcript up to 1200 chars total
    content = summary
    if len(content) < 600 and transcript_text:
        content = content + "\n\n" + transcript_text
    content = content[:1200]

    if not content.strip():
        return {"decisions": [], "blockers": [], "commitments": [], "risks": [],
                "confidence_tone": "neutral"}

    prompt = _EXTRACTION_PROMPT.format(title=title, date=created, content=content)

    try:
        result = _get_llm()(prompt, json_output=True, max_tokens=512)
        if result.get("ok"):
            text = result["text"]
            parsed = json.loads(text) if isinstance(text, str) else text
            return parsed
    except Exception:
        pass

    return {"decisions": [], "blockers": [], "commitments": [], "risks": [],
            "confidence_tone": "neutral"}


def _note_to_transcript_signal(note_id: str, note_meta: dict, extracted: dict) -> TranscriptSignal:
    title = note_meta.get("title") or "Untitled"
    created = (note_meta.get("createdAt") or note_meta.get("created_at") or "")[:10]
    url = note_meta.get("url") or note_meta.get("shareUrl") or None

    decisions = [d.get("text", "") for d in extracted.get("decisions", []) if d.get("text")]
    blockers = [b.get("text", "") for b in extracted.get("blockers", []) if b.get("text")]
    commitments = [c.get("text", "") for c in extracted.get("commitments", []) if c.get("text")]
    risks = [r.get("text", "") for r in extracted.get("risks", []) if r.get("text")]
    tone = extracted.get("confidence_tone", "neutral")

    return TranscriptSignal(
        note_id=note_id,
        title=title,
        note_date=created,
        url=url,
        decisions=decisions,
        blockers=blockers,
        commitments=commitments,
        risks=risks,
        confidence_tone=tone,
    )


# ── Main enrichment ──────────────────────────────────────────────────────────

def enrich_with_granola(project_cards: list, week_start: str) -> tuple[list, list[dict]]:
    """
    Fetch Granola notes from the last 7 days, attribute them to projects,
    extract signals, and attach TranscriptSignals to each ProjectCard.

    Returns (enriched project_cards, cross_project_signals).
    cross_project_signals: notes that couldn't be attributed to any project.
    """
    cross_project: list[dict] = []

    print("  📓 Fetching Granola meeting notes...", file=sys.stderr)
    try:
        notes_result = list_notes(days=7, limit=30)
    except Exception as e:
        print(f"  ⚠️  Granola unavailable: {e}", file=sys.stderr)
        return project_cards, cross_project

    if not notes_result.get("ok"):
        err = notes_result.get("error", "unknown")
        print(f"  ⚠️  Granola error: {err}", file=sys.stderr)
        return project_cards, cross_project

    notes = notes_result.get("notes", [])
    if not notes:
        print("  ℹ️  No Granola notes found for the last 7 days", file=sys.stderr)
        return project_cards, cross_project

    project_names = [c.name for c in project_cards]
    # Build index for O(1) card lookup
    card_by_name = {c.name: c for c in project_cards}

    for note_meta in notes:
        note_id = note_meta.get("id") or note_meta.get("note_id")
        if not note_id:
            continue

        title = note_meta.get("title") or "Untitled"
        folder = note_meta.get("folder") or note_meta.get("folder_name") or ""

        # Fetch full note for transcript/summary content
        try:
            detail_result = get_note(str(note_id), include_transcript=True)
            note_data = detail_result.get("note") or {}
            if not isinstance(note_data, dict):
                note_data = {}
        except Exception:
            note_data = {}

        # Combine meta + detail for attribution
        full_title = note_data.get("title") or title
        content_for_attr = (
            (note_data.get("summary") or "")
            + " "
            + _text_from_transcript(note_data.get("transcript", []))
        )

        attributed_to = _attribute_note(full_title, content_for_attr, folder, project_names)

        # Extract signals regardless of attribution
        extracted = _extract_signals_from_note({**note_meta, **note_data})
        signal = _note_to_transcript_signal(str(note_id), {**note_meta, **note_data}, extracted)

        if attributed_to:
            for proj_name in attributed_to:
                card = card_by_name.get(proj_name)
                if card:
                    card.transcript_signals.append(signal)
                    # Surface the most salient blocker as meeting_signal
                    if signal.blockers and not card.meeting_signal:
                        card.meeting_signal = f'"{signal.blockers[0]}" — {full_title} ({signal.note_date})'
                    elif signal.confidence_tone == "urgent" and not card.meeting_signal:
                        card.meeting_signal = f"Urgent tone in: {full_title} ({signal.note_date})"
                    # Add to card blockers if high-severity
                    urgent_blockers = [
                        b.get("text", "") for b in extracted.get("blockers", [])
                        if b.get("severity") == "high" and b.get("text")
                    ]
                    card.blockers.extend(urgent_blockers)
                    card.evidence.append(Evidence(
                        source="granola",
                        text=f"Meeting: {full_title} ({signal.note_date})",
                        ref=str(note_id),
                        severity="warning" if signal.confidence_tone in ("urgent", "concerned") else "info",
                    ))
        else:
            # Unattributed — goes to cross-project signals
            if extracted.get("decisions") or extracted.get("blockers") or extracted.get("risks"):
                cross_project.append({
                    "note_id": str(note_id),
                    "title": full_title,
                    "note_date": signal.note_date,
                    "url": signal.url,
                    "decisions": signal.decisions,
                    "blockers": signal.blockers,
                    "risks": signal.risks,
                    "confidence_tone": signal.confidence_tone,
                })

    attributed_count = sum(len(c.transcript_signals) for c in project_cards)
    print(f"  ✅ Granola: {len(notes)} notes processed, "
          f"{attributed_count} signals attributed, "
          f"{len(cross_project)} cross-project", file=sys.stderr)

    return project_cards, cross_project
