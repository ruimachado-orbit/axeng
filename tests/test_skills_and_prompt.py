import importlib.util
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def load_orchestrator_module():
    path = ROOT / "src" / "orchestrator.py"
    spec = importlib.util.spec_from_file_location("orchestrator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_axeng_has_core_workflow_skills():
    expected = {
        "granola-api",
        "linear-operations",
        "weekly-team-report",
        "github-team-intelligence",
        "calendar-meeting-prep",
        "team-sync-obsidian",
        "chat-action-items",
        "offboarding",
    }
    found = {p.parent.name for p in (ROOT / "skills").glob("*/*/SKILL.md")}
    assert expected.issubset(found)


def test_all_skills_have_valid_frontmatter():
    skill_files = sorted((ROOT / "skills").glob("*/*/SKILL.md"))
    assert skill_files
    for path in skill_files:
        content = path.read_text()
        assert content.startswith("---"), path
        match = re.search(r"\n---\s*\n", content[3:])
        assert match, path
        frontmatter = yaml.safe_load(content[3:match.start() + 3])
        assert frontmatter["name"] == path.parent.name
        assert frontmatter["description"].startswith("Use when ")
        assert len(frontmatter["description"]) <= 1024
        assert content[match.end() + 3:].strip()


def test_engineering_manager_code_act_prompt_loaded():
    orchestrator = load_orchestrator_module()
    prompt = orchestrator.load_system_prompt()
    assert "Engineering Manager" in prompt
    assert "Code-Act" in prompt
    assert "Delivery risk" in prompt
    assert "Recommended action" in prompt
