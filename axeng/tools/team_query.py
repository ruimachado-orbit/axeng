#!/usr/bin/env python3
"""
Team Intel — Team Query Tool
Query the Obsidian vault for team intelligence.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import vault_path, get, team_members


LAST_SYNC_PATH = Path.home() / ".axeng" / "scripts" / "team-intel" / "last-sync.json"


def read_md(file_path: str) -> str:
    """Read markdown file content."""
    try:
        with open(file_path) as f:
            return f.read()
    except Exception:
        return ""


def get_last_sync_time() -> str:
    """Get last sync timestamp."""
    if not LAST_SYNC_PATH.exists():
        return "Never"
    try:
        with open(LAST_SYNC_PATH) as f:
            data = json.load(f)
            return data.get("timestamp", "Never")
    except Exception:
        return "Never"


def is_vault_configured() -> bool:
    """Check if Obsidian vault is configured."""
    try:
        vault = vault_path()
        return vault and Path(vault).exists()
    except:
        return False


def list_person_profiles() -> list:
    """List all team member profiles."""
    if not is_vault_configured():
        return []

    profiles = []
    vault = vault_path()
    equipa_path = Path(vault) / get("obsidian.team_base", "team/equipa")

    if equipa_path.exists():
        for f in equipa_path.glob("*.md"):
            profiles.append(f.stem)

    return profiles


def get_person_activity(person_name: str) -> dict:
    """Get activity for a specific person."""
    vault = vault_path()
    name_slug = person_name.lower().replace(" ", "-")
    profile_path = Path(vault) / get("obsidian.team_base", "team/equipa") / f"{name_slug}.md"
    
    if profile_path.exists():
        return {
            "name": person_name,
            "profile": read_md(str(profile_path)),
            "status": "found"
        }
    return {"name": person_name, "status": "not_found"}


def get_repo_activity() -> dict:
    """Get activity grouped by repository."""
    vault = vault_path()
    overview_path = Path(vault) / get("obsidian.insights_base", "team/insights") / "team-overview.md"
    
    if overview_path.exists():
        return {
            "content": read_md(str(overview_path)),
            "status": "found"
        }
    return {"status": "not_found"}


def get_metrics() -> dict:
    """Get team metrics."""
    vault = vault_path()
    metrics_path = Path(vault) / get("obsidian.metrics_path", "team/metrics/weekly-metrics.md")
    
    if metrics_path.exists():
        return {
            "metrics": read_md(str(metrics_path)),
            "status": "found"
        }
    return {"status": "not_found"}


def get_blockers() -> dict:
    """Get current blockers from last sync data."""
    if not LAST_SYNC_PATH.exists():
        return {"status": "no_sync_data"}
    
    try:
        with open(LAST_SYNC_PATH) as f:
            data = json.load(f)
            return data.get("github", {})
    except Exception:
        return {}


def team_summary() -> dict:
    """Get full team summary."""
    last_sync = get_last_sync_time()
    profiles = list_person_profiles()
    vault = vault_path()
    
    overview_path = Path(vault) / get("obsidian.insights_base", "team/insights") / "team-overview.md"
    overview = read_md(str(overview_path)) if overview_path.exists() else ""
    
    return {
        "tool": "team_summary",
        "last_sync": last_sync,
        "team_members": profiles,
        "member_count": len(profiles),
        "overview": overview,
        "status": "ready"
    }


def query_person_full(person_name: str) -> str:
    """Get full report for a person including their repos worked."""
    vault = vault_path()
    name_slug = person_name.lower().replace(" ", "-")
    profile_path = Path(vault) / get("obsidian.team_base", "team/equipa") / f"{name_slug}.md"
    
    if not profile_path.exists():
        return f"Persona '{person_name}' não encontrada no vault."
    
    profile = read_md(str(profile_path))
    
    # Enrich with sync data
    if LAST_SYNC_PATH.exists():
        try:
            with open(LAST_SYNC_PATH) as f:
                sync_data = json.load(f)
                github = sync_data.get("github", {})
                
                github_username = person_name.lower().replace(" ", "")
                
                for user, data in github.get("contributors", {}).items():
                    if github_username in user.lower() or user.lower() in github_username:
                        prs = data.get("prs", 0)
                        repos = data.get("repos", [])
                        profile += f"\n\n## Dados GitHub (última sync)\n"
                        profile += f"- PRs mergeados: **{prs}**\n"
                        if repos:
                            profile += f"- Repositórios: {', '.join([f'[[{r}|{r}]]' for r in repos])}\n"
        except Exception:
            pass
    
    return profile


# ─────────────────────────────────────────────
# TOOL: search_vault — Full-text vault search
# ─────────────────────────────────────────────

def search_vault(query: str, max_results: int = 20) -> dict:
    """
    Search vault for query string.
    Returns matching files and context.
    """
    vault = vault_path()
    results = []
    
    for md_file in Path(vault).rglob("*.md"):
        try:
            content = md_file.read_text().lower()
            if query.lower() in content:
                rel_path = md_file.relative_to(vault)
                # Get snippet
                lines = md_file.read_text().split("\n")
                snippets = [l for l in lines if query.lower() in l.lower()][:3]
                results.append({
                    "file": str(rel_path),
                    "matches": snippets
                })
                if len(results) >= max_results:
                    break
        except Exception:
            pass
    
    return {
        "tool": "search_vault",
        "query": query,
        "results": results,
        "count": len(results)
    }


# ─────────────────────────────────────────────
# TOOL: team_member_status — All member statuses
# ─────────────────────────────────────────────

def team_member_status() -> dict:
    """Get status of all team members from profiles."""
    vault = vault_path()
    equipa_path = Path(vault) / get("obsidian.team_base", "team/equipa")
    statuses = []
    
    if not equipa_path.exists():
        return {
            "tool": "team_member_status",
            "status": "equipa_not_found",
            "members": []
        }
    
    for f in equipa_path.glob("*.md"):
        content = read_md(str(f))
        
        # Extract status (look for common patterns)
        status = "unknown"
        if "status:" in content.lower():
            for line in content.split("\n"):
                if "status:" in line.lower():
                    status = line.split("status:")[-1].strip().split()[0] if ":" in line else "unknown"
                    break
        elif "away" in content.lower():
            status = "away"
        elif "OOO" in content or "out of office" in content.lower():
            status = "ooo"
        elif "available" in content.lower() or "active" in content.lower():
            status = "active"
        
        statuses.append({
            "name": f.stem,
            "status": status,
            "file": str(f.relative_to(Path(vault)))
        })
    
    return {
        "tool": "team_member_status",
        "members": statuses,
        "count": len(statuses)
    }


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Check if vault is configured
    if not is_vault_configured():
        data = {
            "available": False,
            "message": "Obsidian vault not configured",
            "setup_instructions": "Set OBSIDIAN_VAULT_PATH in .env or use file-based fallback in $AXENG_HOME/notes/",
            "team_members": [],
            "last_sync": "Never"
        }
        print(json.dumps(data, indent=2, default=str))
        sys.exit(0)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    arg = sys.argv[2] if len(sys.argv) > 2 else ""

    if cmd == "people":
        data = {"people": list_person_profiles()}
    elif cmd == "person":
        data = get_person_activity(arg)
        data["report"] = query_person_full(arg)
    elif cmd == "repos":
        data = get_repo_activity()
    elif cmd == "metrics":
        data = get_metrics()
    elif cmd == "blockers":
        data = get_blockers()
    elif cmd == "search":
        data = search_vault(arg)
    elif cmd == "status":
        data = team_member_status()
    elif cmd == "summary":
        data = team_summary()
    elif cmd == "all":
        data = {
            "summary": team_summary(),
            "metrics": get_metrics(),
            "overview": get_repo_activity()
        }
    else:
        print("Usage: team_query.py [summary|people|person NAME|repos|metrics|blockers|search QUERY|status|all]")
        sys.exit(1)

    print(json.dumps(data, indent=2, default=str))