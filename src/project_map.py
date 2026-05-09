#!/usr/bin/env python3
"""
Team Intel — Project Map
Builds the Linear ↔ GitHub mapping from config.yaml.
Used by weekly_report.py and other tools that need to link
commits/repos to Linear projects and owners.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Resolve config path relative to this file
SCRIPT_DIR = Path(__file__).parent.parent  # src/ → team-intel/
CONFIG_PATH = SCRIPT_DIR / "config" / "config.yaml"


def load_config() -> dict:
    """Load config.yaml, searching up from this file."""
    path = CONFIG_PATH
    for search in [path, Path("config/config.yaml"), Path.cwd() / "config" / "config.yaml"]:
        if Path(search).exists():
            path = search
            break

    if not path.exists():
        raise FileNotFoundError(
            f"config.yaml not found. Copy config/config.yaml.example to config/config.yaml"
        )

    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def build_maps() -> tuple[dict, dict]:
    """
    Returns (LINEAR_GITHUB_MAP, GITHUB_LINEAR_MAP) built from config.yaml.

    LINEAR_GITHUB_MAP:
        "Project Name" → {
            "repos": ["org/repo", ...],
            "owner": "Full Name"
        }

    GITHUB_LINEAR_MAP:
        "org/repo" → {
            "name": "Project Name",
            "owner": "Full Name"
        }
    """
    cfg = load_config()

    linear_map: dict[str, dict] = {}
    github_map: dict[str, dict] = {}

    projects = cfg.get("linear", {}).get("projects", {})
    for proj_name, info in projects.items():
        repos = info.get("repos", [])
        owner = info.get("owner", "Unknown")

        linear_map[proj_name] = {
            "repos": repos,
            "owner": owner,
        }

        for repo in repos:
            github_map[repo] = {
                "name": proj_name,
                "owner": owner,
            }

    return linear_map, github_map


# ── Module-level globals ─────────────────────────────────────────
LINEAR_GITHUB_MAP: dict = {}
GITHUB_LINEAR_MAP: dict = {}

try:
    LINEAR_GITHUB_MAP, GITHUB_LINEAR_MAP = build_maps()
except FileNotFoundError:
    # Config not yet created — maps remain empty; caller should warn
    pass


# ── Convenience helpers ─────────────────────────────────────────

def repos_for_project(project_name: str) -> list:
    """Return the list of GitHub repos for a Linear project."""
    return LINEAR_GITHUB_MAP.get(project_name, {}).get("repos", [])


def owner_of_project(project_name: str) -> str:
    """Return the owner name for a Linear project."""
    return LINEAR_GITHUB_MAP.get(project_name, {}).get("owner", "Unknown")


def project_for_repo(repo: str) -> str | None:
    """Return the Linear project name for a GitHub repo, or None."""
    return GITHUB_LINEAR_MAP.get(repo, {}).get("name")


def owner_of_repo(repo: str) -> str | None:
    """Return the owner name for a GitHub repo, or None."""
    return GITHUB_LINEAR_MAP.get(repo, {}).get("owner")


def all_repos() -> list:
    """Return all unique GitHub repo strings across all projects."""
    seen = set()
    out = []
    for info in LINEAR_GITHUB_MAP.values():
        for r in info.get("repos", []):
            if r not in seen:
                seen.add(r)
                out.append(r)
    return out


def github_orgs() -> list:
    """Return configured GitHub orgs."""
    cfg = load_config()
    return cfg.get("github", {}).get("orgs", [])


def github_name_map() -> dict:
    """Return the GitHub username → display name map."""
    return load_config().get("github", {}).get("name_map", {})


def ex_members() -> set:
    """Return the set of excluded GitHub usernames."""
    return set(load_config().get("github", {}).get("ex_members", []))


def linear_project_ids() -> dict:
    """Return the project name → Linear ID map."""
    return load_config().get("linear", {}).get("project_ids", {})