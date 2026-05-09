#!/usr/bin/env python3
"""
Team Intel — Orchestrator
NL query router: analyze_context + run_tools + synthesize.
Config-driven tool registry and vault path.
"""
import json, os, sys, subprocess
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from config import get, vault_path

TOOLS_DIR = SCRIPT_DIR / "tools"
LAST_SYNC = Path.home() / ".hermes" / "scripts" / "team-intel" / "last-sync.json"


def read_md(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except:
        return ""


# === Tool Registry ===

def load_tool_registry() -> dict:
    """Build TOOLS dict from config.yaml tool_definitions section."""
    raw = get("orchestrator.tools", [])

    # If not defined in config, fall back to built-in defaults
    if not raw:
        return {
            "github_activity": {
                "script": "github_activity.py",
                "args": [],
                "purpose": "Get PRs, reviews, and contribution activity"
            },
            "calendar_insights": {
                "script": "calendar_insights.py",
                "args": ["insights", "7"],
                "purpose": "Get meetings, 1:1s, team events"
            },
            "team_query": {
                "script": "team_query.py",
                "args": [],
                "purpose": "Query Obsidian vault for stored data"
            },
            "linear_issues": {
                "script": "linear_tool.py",
                "args": ["issues", "open"],
                "purpose": "Get Linear issues by state"
            },
            "linear_blockers": {
                "script": "linear_tool.py",
                "args": ["blockers", "7"],
                "purpose": "Get unassigned Linear issues"
            },
            "linear_mine": {
                "script": "linear_tool.py",
                "args": ["mine"],
                "purpose": "Get my assigned Linear issues"
            },
            "linear_sync": {
                "script": "linear_tool.py",
                "args": ["sync"],
                "purpose": "Sync Linear issues to Obsidian vault"
            },
            "sync_all": {
                "script": "team_sync.py",
                "args": [],
                "purpose": "Run full sync: GitHub + Calendar + Email → Obsidian"
            }
        }

    tools = {}
    for entry in raw:
        name = entry.get("name", "")
        if name:
            tools[name] = {
                "script": entry.get("script", ""),
                "args": entry.get("args", []),
                "purpose": entry.get("purpose", "")
            }
    return tools


TOOLS = load_tool_registry()


# === Context Analysis ===

def analyze_context(goal: str) -> list:
    """
    Given a user query/goal, return which tools should run.
    No hard-coded prompts — pure keyword logic.
    """
    goal_lower = goal.lower()
    needed = []

    # GitHub / PR / code activity
    if any(kw in goal_lower for kw in ["pr", "pull request", "review", "github", "contrib", "code", "merge"]):
        needed.append("github_activity")

    # Linear / issues / tasks
    if any(kw in goal_lower for kw in ["linear", "issue", "tarefa", "task", "todo", "blocker", "priority", "estado"]):
        if any(kw in goal_lower for kw in ["meus", "my issues", "assigned", "eu"]):
            needed.append("linear_mine")
        elif any(kw in goal_lower for kw in ["blocker", "unassigned", "sem pessoa"]):
            needed.append("linear_blockers")
        else:
            needed.append("linear_issues")
            needed.append("linear_sync")

    # Calendar / meetings
    if any(kw in goal_lower for kw in ["meeting", "calendar", "standup", "1:1", "one-on-one", "agenda", "schedule"]):
        needed.append("calendar_insights")

    # Email / decisions
    if any(kw in goal_lower for kw in ["email", "decisão", "decision", "inbox", "unread", "thread"]):
        needed.append("email_intel")

    # Vault / team queries
    if any(kw in goal_lower for kw in ["who", "pessoa", "equipa", "team", "resumo", "summary",
                                        "where", "onde", "what", "trabalhar"]):
        needed.append("team_query")

    # Sync requests
    if any(kw in goal_lower for kw in ["sync", "atualizar", "update", "refresh"]):
        needed.append("sync_all")

    return needed if needed else ["team_query"]


# === Tool Execution ===

def run_tool(tool_name: str, args: list = None) -> dict:
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    tool = TOOLS[tool_name]
    script_path = TOOLS_DIR / tool["script"]
    args = args or tool.get("args", [])

    # Fall back to running from SCRIPT_DIR if tools/ subdir doesn't exist
    if not script_path.exists():
        script_path = SCRIPT_DIR / tool["script"]

    try:
        cmd = ["python3", str(script_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except:
                return {"raw": result.stdout, "tool": tool_name}
        else:
            return {"error": result.stderr, "tool": tool_name}
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


# === Response Synthesis ===

def synthesize_results(goal: str, tool_results: list) -> str:
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
                parts.append(f"📋 **Maiolabs — Linear**")
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

    # Rich vault content (non-Linear)
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

    # Default: try to read vault for rich data
    combined = []
    try:
        vault = Path(vault_path())
        overview = vault / get("obsidian.insights_base", "Rui/insights") / "team-overview.md"
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


# === Main Orchestrator ===

def orchestrate(goal: str, auto_sync: bool = True) -> str:
    """
    Main entry point: analyze goal, run tools, synthesize response.
    Optionally auto-sync if vault is stale (>4h).
    """
    print(f"🎯 Orchestrator: {goal}")

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
            print("🔄 Auto-syncing vault...")
            run_tool("sync_all")

    # Dynamic tool selection
    needed_tools = analyze_context(goal)
    print(f"🛠️  Tools selected: {needed_tools}")

    # Execute tools
    results = []
    for tool in needed_tools:
        result = run_tool(tool)
        if result:
            results.append(result)

    # Synthesize response
    response = synthesize_results(goal, results)

    return response


# === CLI ===

if __name__ == "__main__":
    auto = True
    goal_parts = []
    for arg in sys.argv[1:]:
        if arg == "--no-sync":
            auto = False
        else:
            goal_parts.append(arg)
    goal = " ".join(goal_parts) if goal_parts else "team summary"

    response = orchestrate(goal, auto_sync=auto)
    print("\n" + "=" * 50)
    print(response)
    print("=" * 50)