import importlib.util
from pathlib import Path


def load_app_module():
    path = Path(__file__).parents[1] / "ui" / "app.py"
    text = path.read_text()
    return text


def test_ui_has_team_editor_controls():
    text = load_app_module()
    assert "Add Team Member" in text
    assert "Remove selected member" in text
    assert "Team Members" in text


def test_ui_has_linear_project_editor_controls():
    text = load_app_module()
    assert "Add Linear Project" in text
    assert "Project ID" in text
    assert "Repos" in text


def test_ui_has_first_time_setup_wizard():
    text = load_app_module()
    assert "Setup Wizard" in text
    assert "First-time setup" in text


def test_ui_has_raw_yaml_editor_escape_hatch():
    text = load_app_module()
    assert "Advanced: Raw YAML" in text
    assert "yaml.safe_load" in text
