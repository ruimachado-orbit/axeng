#!/usr/bin/env python3
"""
Team Intel — Configuration Loader
Loads config.yaml, provides dot-notation access to settings.
"""
from __future__ import annotations
import os, sys, yaml
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DEFAULT_CONFIG = SCRIPT_DIR.parent / "config" / "config.yaml"


def load(path: str | Path = None) -> dict:
    cfg_path = Path(path) if path else DEFAULT_CONFIG

    if not cfg_path.exists():
        # Check AXENG_HOME first (for Homebrew installs)
        axeng_home = os.getenv("AXENG_HOME")
        search_paths = []

        if axeng_home:
            search_paths.append(Path(axeng_home) / "config" / "config.yaml")
            search_paths.append(Path(axeng_home) / "config.yaml")

        search_paths.extend([
            Path("config/config.yaml"),
            Path.cwd() / "config" / "config.yaml"
        ])

        for search in search_paths:
            if search.exists():
                cfg_path = search
                break

    if not cfg_path.exists():
        raise FileNotFoundError(
            "config.yaml not found. Copy config/config.yaml.example to config/config.yaml"
        )

    with open(cfg_path) as f:
        return yaml.safe_load(f)


_cfg = None


def get(key: str = None, default=None):
    global _cfg
    if _cfg is None:
        try:
            _cfg = load()
        except FileNotFoundError:
            _cfg = {}
    if key is None:
        return _cfg
    parts = key.split(".")
    val = _cfg
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, default)
        else:
            return default
    return val


def github_orgs() -> list:
    return get("github.orgs", [])


_cached_repos = None

def github_repos() -> list:
    """
    Get GitHub repos to analyze.
    Auto-discovers repos if none configured.
    """
    global _cached_repos

    configured = get("github.repos", [])

    if configured:
        return configured

    # Use cache if available
    if _cached_repos is not None:
        return _cached_repos

    # Auto-discover repos using gh CLI
    try:
        import subprocess
        import json

        # Get repos the user has contributed to recently (limit to 10 for speed)
        result = subprocess.run(
            ["gh", "repo", "list", "--limit", "10", "--json", "nameWithOwner"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            repos_data = json.loads(result.stdout)
            discovered = [r["nameWithOwner"] for r in repos_data]
            _cached_repos = discovered
            return discovered
    except:
        pass

    _cached_repos = []
    return []


def github_name_map() -> dict:
    return get("github.name_map", {})


def ex_members() -> set:
    raw = get("github.ex_members", [])
    # Handle both list of strings and list of dicts
    result = set()
    for item in raw:
        if isinstance(item, str):
            result.add(item.lower())
        elif isinstance(item, dict):
            result.add(item.get("name", "").lower())
    return result


def linear_workspace() -> str:
    return get("linear.workspace", "MAI")


def linear_project_ids() -> dict:
    return get("linear.project_ids", {})


def linear_github_map() -> dict:
    return get("linear.projects", {})


def recipients() -> list:
    return get("email.recipients", [])


def email_from() -> str:
    return get("email.from", "")


def vault_path() -> str:
    return os.path.expanduser(get("obsidian.vault_path", "~/Documents/Obsidian Vault"))


def team_members() -> list:
    return get("team", [])


# ── LLM / Provider Settings ───────────────────────────────────────────────────
def llm_provider_order() -> list:
    order = os.environ.get("LLM_PROVIDER_ORDER", "")
    if order:
        return [p.strip() for p in order.split(",") if p.strip()]
    return get("llm.provider_order", [
        "anthropic", "openai", "opencode", "groq",
        "openrouter", "google", "ollama", "lmstudio",
    ])


def llm_default_provider() -> str:
    return get("llm.default_provider", "anthropic")


def llm_max_tokens() -> int:
    return get("llm.max_tokens", int(os.environ.get("LLM_MAX_TOKENS", "4096")))


def llm_temperature() -> float:
    val = get("llm.temperature")
    if val is not None:
        return float(val)
    return float(os.environ.get("LLM_TEMPERATURE", "0.7"))


def llm_model(provider: str) -> str:
    return get(f"llm.{provider}.model") or os.environ.get(f"{provider.upper()}_MODEL", "")


# ── Legacy exports (for scripts that need module-level constants) ─────────────
def _legacy_consts():
    global GITHUB_ORGS, EX_MEMBERS, GITHUB_NAME_MAP, GITHUB_REPOS
    global LINEAR_PROJECT_IDS, LINEAR_GITHUB_MAP, RECIPIENTS, TEAM_MEMBERS

    GITHUB_ORGS = github_orgs()
    EX_MEMBERS = ex_members()
    GITHUB_NAME_MAP = github_name_map()
    GITHUB_REPOS = github_repos()
    LINEAR_PROJECT_IDS = linear_project_ids()
    LINEAR_GITHUB_MAP = linear_github_map()
    RECIPIENTS = recipients()
    TEAM_MEMBERS = team_members()


_legacy_consts()