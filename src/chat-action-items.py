#!/usr/bin/env python3
"""
Axeng — Chat Action Items
Watches a chat-event JSONL feed (e.g. WhatsApp groups exported via the
hermes Baileys bridge), extracts action items via the LLM gateway, files
them as Linear issues in a configurable team, and posts a digest to
Telegram. Idempotent via cursor.

Run: python3 src/chat-action-items.py [--force]

Config (config.yaml):

    chat_action_items:
      enabled: true
      source:
        path: "~/.hermes/state/whatsapp-observed.jsonl"
        cursor_path: "~/.axeng/state/chat-action-cursor.json"
        # Optional URL returning {"groups":[{"id","subject"}]} to resolve
        # chat IDs to friendly names (e.g. http://127.0.0.1:3000/groups
        # for the hermes WhatsApp bridge).
        subjects_url: "http://127.0.0.1:3000/groups"
      # Manual override / fallback for chat name resolution
      chat_subjects:
        "351938240152-1503757297@g.us": "Familia Machado"
      linear:
        team_key: "PER"
        # Whose ID to assign issues to when the LLM classifies owner=="me"
        viewer_self: true   # if true, look up `viewer { id }` and assign
      telegram:
        enabled: true
      window:
        enabled: true
        days: ["mon","tue","wed","thu","fri"]
        start: "08:00"
        end: "19:30"
        tz: "Europe/Lisbon"
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from config import get
from llm_gateway import call_with_fallback

LINEAR_GRAPHQL = "https://api.linear.app/graphql"
HERMES_ENV = Path.home() / ".hermes" / ".env"
DAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def expand(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p)))


def load_env_keys() -> None:
    if not HERMES_ENV.exists():
        return
    for raw in HERMES_ENV.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'").strip('"'))


def in_window(force: bool) -> bool:
    if force:
        return True
    cfg = get("chat_action_items.window", {}) or {}
    if not cfg.get("enabled", True):
        return True
    tz = ZoneInfo(cfg.get("tz", "Europe/Lisbon"))
    now = datetime.datetime.now(tz)
    days = [DAY_INDEX.get(d.lower()) for d in cfg.get("days", ["mon","tue","wed","thu","fri"])]
    if now.weekday() not in days:
        return False
    start = datetime.datetime.strptime(cfg.get("start", "08:00"), "%H:%M").time()
    end = datetime.datetime.strptime(cfg.get("end", "19:30"), "%H:%M").time()
    return start <= now.time() <= end


def load_cursor(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {"offset": 0}


def save_cursor(path: Path, cursor: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cursor))


def read_new(source: Path, cursor: dict) -> tuple[list[dict], dict]:
    if not source.exists():
        return [], cursor
    size = source.stat().st_size
    if size < cursor.get("offset", 0):
        cursor["offset"] = 0
    rows: list[dict] = []
    with source.open("r") as f:
        f.seek(cursor.get("offset", 0))
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        cursor["offset"] = f.tell()
    return rows, cursor


def resolve_subjects() -> dict[str, str]:
    subjects: dict[str, str] = dict(get("chat_action_items.chat_subjects", {}) or {})
    url = get("chat_action_items.source.subjects_url", "")
    if url:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
            for g in data.get("groups", []):
                gid = g.get("id")
                if gid and gid not in subjects:
                    subjects[gid] = g.get("subject") or gid
        except Exception as exc:
            print(f"[chat-action] subjects_url failed: {exc}", file=sys.stderr)
    return subjects


def build_prompt(messages: list[dict], subjects: dict[str, str]) -> str:
    lines = []
    for m in messages:
        chat_id = m.get("chatId", "")
        chat_name = subjects.get(chat_id, chat_id.split("@")[0])
        sender = m.get("pushName") or m.get("senderNumber") or m.get("senderId", "").split("@")[0]
        body = (m.get("body") or "").replace("\n", " ").strip()[:500]
        if not body:
            continue
        prefix = " (me)" if m.get("fromMe") else ""
        flags = []
        if m.get("mentionedJids"):
            flags.append("mention")
        if m.get("quotedParticipant"):
            flags.append("reply")
        flag_str = f" [{','.join(flags)}]" if flags else ""
        lines.append(f"[{chat_name}] {sender}{prefix}: {body}{flag_str}")
    feed = "\n".join(lines)
    return (
        "You receive recent messages from chat groups the user participates in.\n"
        "Identify ACTION ITEMS — things someone said need to get done: requests, "
        "questions that need answering, deadlines, events to confirm, decisions, "
        "errands. Ignore chit-chat, photos without context, thanks, social talk.\n\n"
        "For each item classify:\n"
        '  owner: "me" if clearly the user (marked "(me)") must do it, '
        '"other" if someone else, "unknown" if unclear.\n'
        '  urgency: "high" (urgent / short deadline), "normal", "low".\n\n'
        "Return ONLY a JSON array, no prose, no markdown fences. Each element:\n"
        '{"summary": short title (max 80 chars), '
        '"owner": "me"|"other"|"unknown", '
        '"urgency": "high"|"normal"|"low", '
        '"group": chat name, '
        '"source": short quote of the original message (max 200 chars)}\n'
        "If no action items, return [].\n\n"
        f"Messages (oldest first):\n{feed}"
    )


def parse_items(text: str) -> list[dict]:
    if not text:
        return []
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    match = re.search(r"\[[\s\S]*\]", cleaned)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        print(f"[chat-action] LLM JSON parse failed: {exc}\nraw: {text[:500]}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        return []
    items: list[dict] = []
    for it in data:
        if not isinstance(it, dict) or not it.get("summary"):
            continue
        items.append(
            {
                "summary": str(it["summary"])[:200],
                "owner": str(it.get("owner") or "unknown").lower(),
                "urgency": str(it.get("urgency") or "normal").lower(),
                "group": str(it.get("group") or ""),
                "source": str(it.get("source") or "")[:500],
            }
        )
    return items


def linear_gql(query: str, variables: dict | None = None) -> dict:
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        return {"errors": [{"message": "LINEAR_API_KEY not set"}]}
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        LINEAR_GRAPHQL,
        data=body,
        headers={"Authorization": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        return {"errors": [{"message": str(exc)}]}


def linear_team_id(team_key: str) -> str | None:
    res = linear_gql("query($k:String!){ teams(filter:{key:{eq:$k}}){ nodes { id key } } }", {"k": team_key})
    nodes = (res.get("data") or {}).get("teams", {}).get("nodes", [])
    return nodes[0]["id"] if nodes else None


def linear_viewer_id() -> str | None:
    res = linear_gql("query { viewer { id } }")
    return (res.get("data") or {}).get("viewer", {}).get("id")


URGENCY_TO_PRIORITY = {"high": 2, "normal": 3, "low": 4}


def create_linear_issue(team_id: str, viewer_id: str | None, item: dict) -> dict | None:
    description_lines = [
        f"**Group:** {item.get('group') or '—'}",
        f"**Owner (LLM-classified):** {item.get('owner')}",
    ]
    if item.get("source"):
        description_lines.append(f"\n**Source:**\n> {item['source']}")
    description_lines.append("\n_Auto-created by Axeng · chat-action-items._")
    input_data: dict = {
        "teamId": team_id,
        "title": item["summary"],
        "description": "\n".join(description_lines),
        "priority": URGENCY_TO_PRIORITY.get(item.get("urgency", "normal"), 0),
    }
    assign_self = bool(get("chat_action_items.linear.viewer_self", True))
    if item.get("owner") == "me" and viewer_id and assign_self:
        input_data["assigneeId"] = viewer_id

    mutation = """
    mutation Create($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier url title }
      }
    }
    """
    res = linear_gql(mutation, {"input": input_data})
    payload = (res.get("data") or {}).get("issueCreate") or {}
    if not payload.get("success"):
        print(f"[chat-action] issueCreate failed: {res}", file=sys.stderr)
        return None
    return payload.get("issue")


def md_escape(text: str) -> str:
    return text.replace("_", r"\_").replace("*", r"\*").replace("[", r"\[").replace("`", r"\`")


OWNER_LABEL = {"me": "📌 me", "other": "👥 other", "unknown": "❓ unclear"}
URGENCY_BADGE = {"high": "🔴", "normal": "", "low": "⚪️"}


def format_telegram(items_with_issues: list[tuple[dict, dict | None]], total_msgs: int) -> str:
    if not items_with_issues:
        return ""
    header = f"📱 *Chat action items* — {len(items_with_issues)} item(s) from {total_msgs} msg(s)"
    out = [header, ""]
    for item, issue in items_with_issues:
        badge = URGENCY_BADGE.get(item.get("urgency"), "")
        owner = OWNER_LABEL.get(item.get("owner"), "")
        group = md_escape(item.get("group", ""))
        summary = md_escape(item["summary"])
        link = f" [{issue['identifier']}]({issue['url']})" if issue else ""
        line = f"{badge} \\[{group}\\] {summary}{link} — {owner}".strip()
        out.append(f"- {line}")
    return "\n".join(out)


def send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(text)  # cron picks this up
        return False
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=payload)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True
    except Exception as exc:
        print(f"[chat-action] telegram failed: {exc}", file=sys.stderr)
        print(text)
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Bypass time-window gate")
    parser.add_argument("--dry-run", action="store_true", help="Skip Linear create + Telegram, print result")
    args = parser.parse_args()

    load_env_keys()

    if not get("chat_action_items.enabled", False):
        print("[chat-action] disabled in config.yaml (chat_action_items.enabled=false). Skipping.")
        return 0

    if not in_window(args.force):
        return 0

    source = expand(get("chat_action_items.source.path", "~/.hermes/state/whatsapp-observed.jsonl"))
    cursor_path = expand(get("chat_action_items.source.cursor_path", "~/.axeng/state/chat-action-cursor.json"))

    cursor = load_cursor(cursor_path)
    messages, cursor = read_new(source, cursor)
    if not messages:
        save_cursor(cursor_path, cursor)
        return 0

    subjects = resolve_subjects()
    prompt = build_prompt(messages, subjects)
    llm = call_with_fallback(prompt, max_tokens=2048, temperature=0.2, json_output=True)
    if not llm.get("ok"):
        print(f"[chat-action] LLM call failed: {llm.get('error')}", file=sys.stderr)
        # Don't advance cursor — retry next run
        return 1
    items = parse_items(llm.get("text", ""))

    if args.dry_run:
        print(json.dumps({"messages": len(messages), "items": items}, indent=2))
        return 0

    team_key = get("chat_action_items.linear.team_key", "")
    team_id = linear_team_id(team_key) if team_key else None
    viewer_id = linear_viewer_id() if items else None

    items_with_issues: list[tuple[dict, dict | None]] = []
    for item in items:
        issue = create_linear_issue(team_id, viewer_id, item) if team_id else None
        items_with_issues.append((item, issue))

    if items_with_issues and get("chat_action_items.telegram.enabled", True):
        text = format_telegram(items_with_issues, len(messages))
        if text:
            send_telegram(text)

    save_cursor(cursor_path, cursor)
    return 0


if __name__ == "__main__":
    sys.exit(main())
