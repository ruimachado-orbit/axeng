#!/usr/bin/env python3
"""
Team Intel — Orchestrator
NL query router: analyze_context + run_tools + synthesize.
Config-driven tool registry and vault path.
Optional LLM synthesis via llm_gateway (anthropic, openai, opencode,
ollama, lmstudio, groq, openrouter, google).
"""
import json, os, sys, subprocess, time
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from config import get, vault_path, llm_provider_order, llm_default_provider, llm_max_tokens, llm_temperature
from llm_gateway import call_with_fallback, status as llm_status, get_available_providers

TOOLS_DIR = SCRIPT_DIR / "tools"
SYSTEM_PROMPT_PATH = SCRIPT_DIR.parent / "prompts" / "engineering-manager-code-act.md"
LAST_SYNC = Path.home() / ".axeng" / "scripts" / "team-intel" / "last-sync.json"


def read_md(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except:
        return ""


def load_system_prompt() -> str:
    """Load the Engineering Manager code-act system prompt with a safe fallback."""
    prompt = read_md(str(SYSTEM_PROMPT_PATH)).strip()
    if prompt:
        return prompt
    return (
        "You are Axeng, an expert Engineering Manager AI assistant. "
        "You help EMs with team management, project status, standups, reports, and decisions. "
        "Act on available tool results, be concise and specific, name owners and next actions, "
        "push back on delivery risk, and never invent missing data."
    )


# ── Tool Registry ─────────────────────────────────────────────────────────────
def load_tool_registry() -> dict:
    """Build TOOLS dict from config.yaml tool_definitions section."""
    raw = get("orchestrator.tools", [])

    if not raw:
        return {
            "github_activity": {
                "script": "github_activity.py",
                "args": [],
                "purpose": "Get PRs, reviews, and contribution activity",
            },
            "calendar_insights": {
                "script": "calendar_insights.py",
                "args": ["insights", "7"],
                "purpose": "Get meetings, 1:1s, team events",
            },
            "team_query": {
                "script": "team_query.py",
                "args": [],
                "purpose": "Query Obsidian vault for stored data",
            },
            "linear_issues": {
                "script": "linear_tool.py",
                "args": ["issues", "open"],
                "purpose": "Get Linear issues by state",
            },
            "linear_blockers": {
                "script": "linear_tool.py",
                "args": ["blockers", "7"],
                "purpose": "Get unassigned Linear issues",
            },
            "linear_mine": {
                "script": "linear_tool.py",
                "args": ["mine"],
                "purpose": "Get my assigned Linear issues",
            },
            "linear_sync": {
                "script": "linear_tool.py",
                "args": ["sync"],
                "purpose": "Sync Linear issues to Obsidian vault",
            },
            "vacations": {
                "script": "vacations.py",
                "args": ["list"],
                "purpose": "Get team vacations/PTO from Linear (who is OOO)",
            },
            "granola_notes": {
                "script": "granola_tool.py",
                "args": ["notes", "--days", "30", "--limit", "20"],
                "purpose": "List recent Granola meeting notes",
            },
            "granola_latest": {
                "script": "granola_tool.py",
                "args": ["latest", "--days", "30", "--transcript"],
                "purpose": "Fetch the latest Granola note with transcript",
            },
            "granola_folders": {
                "script": "granola_tool.py",
                "args": ["folders"],
                "purpose": "List Granola folders",
            },
            "granola_export": {
                "script": "granola_tool.py",
                "args": ["export", "--days", "30"],
                "purpose": "Export recent Granola notes and transcripts to Markdown",
            },
            "sync_all": {
                "script": "team_sync.py",
                "args": [],
                "purpose": "Run full sync: GitHub + Calendar + Email → Obsidian",
            },
        }

    tools = {}
    for entry in raw:
        name = entry.get("name", "")
        if name:
            tools[name] = {
                "script": entry.get("script", ""),
                "args": entry.get("args", []),
                "purpose": entry.get("purpose", ""),
            }
    return tools


TOOLS = load_tool_registry()


# ── Context Analysis ──────────────────────────────────────────────────────────
def analyze_context(goal: str) -> list:
    """
    Given a user query/goal, return which tools should run.
    No hard-coded prompts — pure keyword logic.
    """
    goal_lower = goal.lower()
    needed = []

    if any(kw in goal_lower for kw in ["pr", "pull request", "review", "github", "contrib", "code", "merge"]):
        needed.append("github_activity")

    if any(kw in goal_lower for kw in ["linear", "issue", "tarefa", "task", "todo", "blocker", "priority", "estado"]):
        if any(kw in goal_lower for kw in ["meus", "my issues", "assigned", "eu"]):
            needed.append("linear_mine")
        elif any(kw in goal_lower for kw in ["blocker", "unassigned", "sem pessoa"]):
            needed.append("linear_blockers")
        else:
            needed.append("linear_issues")
            needed.append("linear_sync")

    if any(kw in goal_lower for kw in ["meeting", "calendar", "standup", "1:1", "one-on-one", "agenda", "schedule"]):
        needed.append("calendar_insights")

    if any(kw in goal_lower for kw in [
        "granola", "transcript", "transcription", "transcrições", "transcricoes",
        "meeting notes", "meeting note", "call notes", "notes from", "notas da reunião",
        "notas de reunião", "resumo da reunião"
    ]):
        if any(kw in goal_lower for kw in ["latest", "last", "recent", "summarize", "summary", "transcript", "transcrição", "transcricao", "resumo"]):
            needed.append("granola_latest")
        else:
            needed.append("granola_notes")
        if any(kw in goal_lower for kw in ["export", "markdown", "save", "guardar", "download"]):
            needed.append("granola_export")

    if any(kw in goal_lower for kw in ["email", "decisão", "decision", "inbox", "unread", "thread"]):
        needed.append("email_intel")

    if any(kw in goal_lower for kw in ["who", "pessoa", "equipa", "team", "resumo", "summary",
                                        "where", "onde", "what", "trabalhar"]):
        needed.append("team_query")

    if any(kw in goal_lower for kw in ["sync", "atualizar", "update", "refresh"]):
        needed.append("sync_all")

    return needed if needed else ["team_query"]


# ── Tool Execution ─────────────────────────────────────────────────────────────
def run_tool(tool_name: str, args: list = None, quiet: bool = False) -> dict:
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    tool = TOOLS[tool_name]
    script_path = TOOLS_DIR / tool["script"]
    args = args or tool.get("args", [])

    if not script_path.exists():
        script_path = SCRIPT_DIR / tool["script"]

    # Show progress indicator
    if not quiet:
        purpose = tool.get("purpose", tool_name)
        print(f"  🔍 Querying {tool_name}... ({purpose})")

    start_time = time.time()

    try:
        cmd = ["python3", str(script_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        elapsed = time.time() - start_time

        if result.returncode == 0:
            if not quiet:
                print(f"     ✓ Completed in {elapsed:.2f}s")
            try:
                data = json.loads(result.stdout)
                data["_execution_time"] = round(elapsed, 2)
                return data
            except:
                return {"raw": result.stdout, "tool": tool_name, "_execution_time": round(elapsed, 2)}
        else:
            if not quiet:
                print(f"     ✗ Failed after {elapsed:.2f}s")
            return {"error": result.stderr, "tool": tool_name, "_execution_time": round(elapsed, 2)}
    except Exception as e:
        elapsed = time.time() - start_time
        if not quiet:
            print(f"     ✗ Error after {elapsed:.2f}s")
        return {"error": str(e), "tool": tool_name, "_execution_time": round(elapsed, 2)}


# ── LLM Synthesis ─────────────────────────────────────────────────────────────
def llm_synthesize(goal: str, tool_results: list, provider: str = None, quiet: bool = False) -> str:
    """
    Use the LLM gateway to synthesize a response from tool results.
    Falls back to the logic-driven synthesizer if LLM is unavailable.
    """
    # Format tool results for the LLM
    results_text = _format_tool_results(tool_results)

    # Try to read vault context
    vault_context = _get_vault_context(goal)

    system = load_system_prompt()

    vault_section = f"Vault Context:\n{vault_context}" if vault_context else ""
    prompt = f"""Goal: {goal}

Tool Results:
{results_text}

{vault_section}

Synthesize a clear, actionable response to the goal above. """
    if "summary" in goal.lower() or "team" in goal.lower() or "equipa" in goal.lower():
        prompt += (
            "Include: key metrics, notable blockers, recent wins, and next steps. "
            "Mention specific names, PR numbers, and dates where available."
        )
    elif "standup" in goal.lower() or "daily" in goal.lower():
        prompt += (
            "Structure as a standup report: what shipped, what's in progress, blockers, "
            "who is OOO, and relevant PRs."
        )
    elif "risk" in goal.lower() or "radar" in goal.lower():
        prompt += (
            "List risks with severity (🔴 high, 🟡 medium, 🟢 low), owner, and suggested action."
        )

    providers = llm_provider_order()
    if provider:
        providers = [p for p in providers if p == provider] + providers

    if not quiet:
        print(f"\n🤖 Synthesizing response with LLM...")

    start_time = time.time()

    result = call_with_fallback(
        prompt,
        providers=providers,
        system=system,
        max_tokens=llm_max_tokens(),
        temperature=llm_temperature(),
        json_output=False,
    )

    elapsed = time.time() - start_time

    if result.get("ok"):
        if not quiet:
            model_used = result.get("model", "unknown")
            prov = result.get("provider", "unknown")
            print(f"   ✓ Completed in {elapsed:.2f}s using {prov}/{model_used}")
        return result["text"]

    # Fall back to logic-driven synthesis
    if not quiet:
        print(f"   ✗ LLM unavailable ({result.get('error', 'unknown')}) — using rule-based synthesis")
    return _synthesize_logic(goal, tool_results)


def _format_tool_results(results: list) -> str:
    """Format tool results for LLM prompt."""
    parts = []
    for r in results:
        if not isinstance(r, dict):
            parts.append(str(r))
            continue
        tool = r.get("tool", "unknown")
        if "error" in r and not r.get("raw"):
            parts.append(f"[{tool}] ERROR: {r['error']}")
            continue
        parts.append(f"[{tool}]")
        for k, v in r.items():
            if k == "tool":
                continue
            if isinstance(v, (list, dict)):
                parts.append(f"  {k}: {json.dumps(v, ensure_ascii=False)[:500]}")
            else:
                parts.append(f"  {k}: {str(v)[:500]}")
    return "\n".join(parts) if parts else "(no results)"


def _get_vault_context(goal: str) -> str:
    """Grab relevant vault content based on goal keywords."""
    try:
        vault = Path(vault_path())
        snippets = []
        goal_lower = goal.lower()

        if any(k in goal_lower for k in ["team", "equipa", "member", "pessoa"]):
            for f in vault.rglob("team-overview.md"):
                content = read_md(str(f))[:1000]
                if content:
                    snippets.append(content)

        if any(k in goal_lower for k in ["sprint", "project", "roadmap"]):
            for f in vault.rglob("sprint*.md"):
                content = read_md(str(f))[:800]
                if content:
                    snippets.append(content)

        return "\n\n".join(snippets)[:2000] if snippets else ""
    except:
        return ""


# ── Logic-Driven Synthesis (fallback) ─────────────────────────────────────────
def _synthesize_logic(goal: str, tool_results: list) -> str:
    """
    Combine results from multiple tools into a coherent response.
    Logic-driven: no LLM, no prompts.
    """
    goal_lower = goal.lower()

    # Linear-first synthesis
    linear_results = [
        r for r in tool_results
        if isinstance(r, dict) and r.get("tool", "").startswith("linear")
    ]
    if linear_results:
        parts = []
        for result in tool_results:
            if not isinstance(result, dict):
                continue
            tool = result.get("tool", "")
            if tool == "linear_summary":
                parts.append(f"📋 **Axeng — Linear**")
                parts.append(f"  • Todo: {result.get('metrics', {}).get('todo', 0)}")
                parts.append(f"  • In Progress: {result.get('metrics', {}).get('in_progress', 0)}")
                parts.append(f"  • My tasks: {result.get('my_tasks', 0)}")
                parts.append(f"  • Blockers: {result.get('blockers', 0)}")
            elif tool == "linear_issues":
                by_state = result.get("by_state", {})
                for state, items in by_state.items():
                    if items:
                        parts.append(f"\n**{state} ({len(items)})**")
                        for item in items[:5]:
                            parts.append(f"  • {item}")
            elif tool == "linear_my_issues":
                total = result.get("total", 0)
                by_state = result.get("by_state", {})
                parts.append(f"\n👤 **As Minhas Tarefas ({total})**")
                for state, items in by_state.items():
                    if items:
                        parts.append(f"  [{state}]: {len(items)}")
            elif tool == "linear_blockers":
                count = result.get("recent_unassigned", 0)
                issues = result.get("issues", [])
                if issues:
                    parts.append(f"\n⚠️ **Blockers ({count})**")
                    for item in issues[:5]:
                        parts.append(f"  • {item}")
                else:
                    parts.append(f"\n✅ Sem blockers nos últimos 7 dias")
        if parts:
            return "\n".join(parts)

    # Granola notes / transcripts
    granola_results = [
        r for r in tool_results
        if isinstance(r, dict) and r.get("tool", "").startswith("granola")
    ]
    if granola_results:
        parts = ["🎙️ **Granola**"]
        for result in granola_results:
            tool = result.get("tool", "")
            if tool == "granola_notes":
                notes = result.get("notes", [])
                parts.append(f"• Notes found: {result.get('count', len(notes))}")
                for note in notes[:5]:
                    title = note.get("title") or note.get("name") or note.get("id") or "Untitled note"
                    note_id = note.get("id") or note.get("note_id") or ""
                    created = note.get("createdAt") or note.get("created_at") or note.get("updatedAt") or ""
                    parts.append(f"  - {title} `{note_id}` {created}")
            elif tool in ("granola_note", "granola_latest"):
                note = result.get("note") or {}
                title = note.get("title") or result.get("note_id")
                summary = note.get("summary") or note.get("summary_text") or note.get("summary_markdown") or note.get("overview") or ""
                parts.append(f"• {title}")
                if summary:
                    parts.append(str(summary)[:1200])
                parts.append(f"• Transcript items: {result.get('transcript_items', 0)}")
            elif tool == "granola_export":
                files = result.get("files", [])
                parts.append(f"• Exported {len(files)} files")
                for path in files[:5]:
                    parts.append(f"  - `{path}`")
            elif result.get("error") or result.get("raw"):
                raw = result.get("raw") or result
                parts.append(f"• Error: {raw.get('error', 'unknown')}")
        return "\n".join(parts)

    # Rich vault content
    for result in tool_results:
        if isinstance(result, dict):
            if "member_count" in result and result.get("overview"):
                return result["overview"]
            if "summary" in result and isinstance(result["summary"], dict):
                if result["summary"].get("overview"):
                    return result["summary"]["overview"]
            if "overview" in result and result["overview"]:
                return result["overview"]
            if "content" in result and result["content"]:
                return result["content"]

    # PR / activity summary
    if any(kw in goal_lower for kw in ["pr", "activity"]):
        parts = []
        for result in tool_results:
            if "pulls" in result:
                pulls = result.get("pulls", [])
                if pulls:
                    parts.append(f"**{len(pulls)} PRs encontrados**")
                    for pr in pulls[:5]:
                        parts.append(f"• #{pr['number']} {pr['title'][:50]}... [[{pr['repo']}]]")
            if "contributors" in result:
                for user, data in result["contributors"].items():
                    repos = ", ".join(data.get("repos", [])[:3])
                    parts.append(f"@{user}: **{data['prs']} PRs** em {repos}")
        return "\n".join(parts) if parts else "Sem dados de PRs."

    # Meeting summary
    if any(kw in goal_lower for kw in ["meeting", "calendar"]):
        parts = []
        for result in tool_results:
            if "1on1s" in result:
                ones = result["1on1s"]
                if ones:
                    parts.append(f"**{len(ones)} 1:1s esta semana:**")
                    for m in ones[:3]:
                        parts.append(f"• {m['title']}")
            if "team_meetings" in result:
                meets = result["team_meetings"]
                if meets:
                    parts.append(f"\n**{len(meets)} reuniões de equipa:**")
                    for m in meets[:3]:
                        parts.append(f"• {m['title']}")
        return "\n".join(parts) if parts else "Sem reuniões."

    # Person / team summary
    if any(kw in goal_lower for kw in ["who", "pessoa", "member", "equipa", "team", "summary"]):
        for result in tool_results:
            if "report" in result:
                return result["report"]
            if "people" in result:
                people = result["people"]
                if people:
                    return f"**{len(people)} membros:** " + ", ".join(people)
            if "member_count" in result:
                return f"**Team Intel — {result['member_count']} membros**\n\nLast sync: {result.get('last_sync', 'Never')}"
        return "Sem dados da equipa."

    # Default: try vault
    combined = []
    try:
        vault = Path(vault_path())
        overview = vault / get("obsidian.insights_base", "team/insights") / "team-overview.md"
        if overview.exists():
            content = read_md(str(overview))
            if content:
                combined.append(content)
    except:
        pass

    for result in tool_results:
        if isinstance(result, dict):
            if "pulls" in result:
                combined.append(f"PRs: {len(result.get('pulls', []))}")
            elif "1on1s" in result:
                combined.append(f"1:1s: {len(result.get('1on1s', []))}")
            elif "error" in result:
                combined.append(f"Erro: {result['error']}")

    return "\n".join(combined) if combined else "Sem dados."


# ── Main Orchestrator ──────────────────────────────────────────────────────────
def orchestrate(goal: str, auto_sync: bool = True, use_llm: bool = True,
                provider: str = None, dry: bool = False, quiet: bool = False) -> str:
    """
    Main entry point: analyze goal, run tools, synthesize response.

    Args:
        goal: Natural language query
        auto_sync: Auto-sync vault if stale (>4h)
        use_llm: Use LLM gateway for synthesis (default True)
        provider: Force a specific provider (None = use fallback order)
        dry: Run tools but skip synthesis (for debugging)
        quiet: Suppress debug output (for CLI chat mode)
    """
    if not quiet:
        print(f"🎯 Orchestrator: {goal}")
    if dry:
        if not quiet:
            print("  [DRY MODE — skipping synthesis]")
        use_llm = False

    # Auto-sync if vault is stale
    if auto_sync:
        try:
            with open(LAST_SYNC) as f:
                sync_data = json.load(f)
            last_sync = datetime.fromisoformat(sync_data.get("timestamp", "2020-01-01"))
            needs_sync = (datetime.now() - last_sync).total_seconds() > 4 * 3600
        except:
            needs_sync = True

        if needs_sync:
            if not quiet:
                print("🔄 Auto-syncing vault...")
            run_tool("sync_all")

    # Dynamic tool selection
    needed_tools = analyze_context(goal)
    if not quiet:
        print(f"🛠️  Tools selected: {needed_tools}")

    # Execute tools
    results = []
    if not quiet:
        print(f"\n📦 Executing {len(needed_tools)} tool(s)...\n")

    for tool in needed_tools:
        result = run_tool(tool, quiet=quiet)
        if result:
            results.append(result)

    if not quiet:
        total_time = sum(r.get("_execution_time", 0) for r in results)
        print(f"\n⏱️  Total tool execution time: {total_time:.2f}s")

    if dry:
        print("\n--- Tool Results ---")
        for r in results:
            print(json.dumps(r, indent=2, ensure_ascii=False)[:300])
        return "(dry run — no synthesis)"

    # Synthesize
    if use_llm:
        response = llm_synthesize(goal, results, provider=provider, quiet=quiet)
    else:
        response = _synthesize_logic(goal, results)

    return response


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    auto = True
    use_llm = True
    dry = False
    provider = None
    goal_parts = []

    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--no-sync":
            auto = False
        elif arg == "--no-llm":
            use_llm = False
        elif arg == "--llm":
            use_llm = True
        elif arg == "--dry":
            dry = True
        elif arg == "--provider" and i + 1 < len(sys.argv[1:]):
            provider = sys.argv[1:][i + 2]  # next arg after --provider
            sys.argv = sys.argv[:i + 2] + sys.argv[i + 3:]
        elif arg in ("--status", "-s"):
            # LLM status
            st = llm_status()
            print(json.dumps(st, indent=2))
            sys.exit(0)
        else:
            goal_parts.append(arg)

    goal = " ".join(goal_parts) if goal_parts else "team summary"
    response = orchestrate(goal, auto_sync=auto, use_llm=use_llm, provider=provider, dry=dry)
    print("\n" + "=" * 50)
    print(response)
    print("=" * 50)