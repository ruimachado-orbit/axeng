"""
Tests for the CEO steering report — schema, aggregator, scoring, persistence.
Run with: pytest tests/test_steering_report.py -v
"""
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Load modules under test directly (no package install needed)
_ROOT = Path(__file__).parents[1] / "axeng"
sys.path.insert(0, str(_ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # required for dataclass type resolution in Python 3.14+
    spec.loader.exec_module(mod)
    return mod


# ── Schema ────────────────────────────────────────────────────────────────────

def test_steering_report_serialises_to_dict():
    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    report = schema.SteeringReport(
        report_id="steering-2026-05-30",
        generated_at="2026-05-30T08:00:00",
        week_start="2026-05-26",
        week_end="2026-05-30",
    )
    d = schema.report_to_dict(report)
    assert d["report_id"] == "steering-2026-05-30"
    assert d["week_end"] == "2026-05-30"
    # Ensure JSON-serialisable (no dataclass objects)
    json.dumps(d)


def test_project_card_defaults():
    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    card = schema.ProjectCard(name="Alpha", owner="João")
    assert card.status == "on_track"
    assert card.blockers == []
    assert card.evidence == []


def test_report_to_dict_nested():
    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    card = schema.ProjectCard(
        name="Beta", owner="Ana",
        linear_signals=schema.LinearSignals(completion_rate=60.0, velocity=0.8),
        issue_signals=schema.IssueSignals(stale_count=3, risk_score=25.0),
    )
    report = schema.SteeringReport(
        report_id="steering-2026-05-30",
        generated_at="2026-05-30T08:00:00",
        week_start="2026-05-26",
        week_end="2026-05-30",
        projects=[card],
    )
    d = schema.report_to_dict(report)
    proj = d["projects"][0]
    assert proj["linear_signals"]["completion_rate"] == 60.0
    assert proj["issue_signals"]["stale_count"] == 3


# ── Week boundaries ───────────────────────────────────────────────────────────

def test_week_boundaries_snaps_to_friday():
    # Import steering_report — patch heavy imports
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    monday, friday = sr._week_boundaries(date(2026, 5, 28))  # Wednesday
    assert friday.weekday() == 4, "week_end must be Friday"
    assert monday.weekday() == 0, "week_start must be Monday"
    assert (friday - monday).days == 4


def test_week_boundaries_on_friday():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    monday, friday = sr._week_boundaries(date(2026, 5, 29))  # Friday
    assert friday == date(2026, 5, 29)
    assert monday == date(2026, 5, 25)


# ── Timeline calculations ─────────────────────────────────────────────────────

def test_timeline_metrics_no_target():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    result = sr._timeline_metrics(None, None)
    assert result["days_left"] is None
    assert result["time_progress_pct"] == 0.0


def test_timeline_metrics_with_dates():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    future = (date.today() + timedelta(days=30)).isoformat()
    past = (date.today() - timedelta(days=30)).isoformat()
    result = sr._timeline_metrics(past, future)
    assert result["days_left"] == 30
    assert 40 < result["time_progress_pct"] < 60  # ~50% elapsed


def test_compute_timeline_position():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    assert sr._compute_timeline_position(50, 60) == "ahead"      # work > time
    assert sr._compute_timeline_position(50, 45) == "on_plan"    # gap within tolerance
    assert sr._compute_timeline_position(50, 30) == "behind"     # -20 gap
    assert sr._compute_timeline_position(60, 25) == "significantly_behind"  # -35 gap


# ── Scoring ───────────────────────────────────────────────────────────────────

def test_score_on_track_project():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    linear = schema.LinearSignals(completion_rate=85, staleness_rate=5, velocity=2.0)
    issues = schema.IssueSignals(risk_score=5)
    score, confidence, status, forecast = sr._score_project(linear, issues, 60, 85, [])
    assert status == "on_track"
    assert confidence == "high"
    assert score > 75


def test_score_urgent_transcript_caps_status():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    linear = schema.LinearSignals(completion_rate=80, staleness_rate=5, velocity=2.0)
    issues = schema.IssueSignals(risk_score=5)
    urgent = schema.TranscriptSignal(
        note_id="n1", title="Urgent meeting", note_date="2026-05-28",
        confidence_tone="urgent"
    )
    score, confidence, status, forecast = sr._score_project(linear, issues, 50, 80, [urgent])
    assert status in ("at_risk", "off_track")
    assert score <= 59


def test_score_declining_velocity_nudges_down():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    linear = schema.LinearSignals(completion_rate=80, staleness_rate=10, velocity=1.5)
    issues = schema.IssueSignals(risk_score=10)

    score_stable, _, _, _ = sr._score_project(linear, issues, 55, 78, [], velocity_trend="stable")
    score_declining, _, _, _ = sr._score_project(linear, issues, 55, 78, [], velocity_trend="declining")
    score_improving, _, _, _ = sr._score_project(linear, issues, 55, 78, [], velocity_trend="improving")

    assert score_declining < score_stable
    assert score_improving > score_stable
    assert score_declining == score_stable - 8
    assert score_improving == score_stable + 5


def test_score_declining_velocity_can_flip_status():
    """A borderline on_track project should drop to at_risk if velocity is declining."""
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    # Inputs that produce a score just above 75 with stable velocity
    linear = schema.LinearSignals(completion_rate=84, staleness_rate=8, velocity=1.5)
    issues = schema.IssueSignals(risk_score=5)

    score_stable, _, status_stable, _ = sr._score_project(linear, issues, 55, 80, [], velocity_trend="stable")
    score_declining, _, status_declining, _ = sr._score_project(linear, issues, 55, 80, [], velocity_trend="declining")

    # Verify the stable score is actually above the threshold before asserting status
    assert score_stable >= 75, f"Test setup issue: stable score {score_stable} < 75"
    assert score_declining < score_stable

    assert status_stable == "on_track"
    assert status_declining == "at_risk"


# ── SprintSignals schema ──────────────────────────────────────────────────────

def test_sprint_signals_defaults():
    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    sp = schema.SprintSignals()
    assert sp.velocity_trend == "stable"
    assert sp.velocity_avg == 0.0
    assert sp.sprint_status == "unknown"


def test_sprint_signals_in_report_dict():
    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    sp = schema.SprintSignals(
        sprint_name="Sprint 42",
        velocity_trend="declining",
        velocity_avg=1.8,
        cycles_analyzed=5,
    )
    report = schema.SteeringReport(
        report_id="steering-2026-05-30",
        generated_at="2026-05-30T08:00:00",
        week_start="2026-05-26",
        week_end="2026-05-30",
        sprint_signals=sp,
    )
    d = schema.report_to_dict(report)
    assert d["sprint_signals"]["sprint_name"] == "Sprint 42"
    assert d["sprint_signals"]["velocity_trend"] == "declining"
    assert d["sprint_signals"]["velocity_avg"] == 1.8


def test_score_missing_owner_triggers_unowned_forecast():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    linear = schema.LinearSignals(completion_rate=20, staleness_rate=70, velocity=0.1)
    issues = schema.IssueSignals(unowned_count=5, risk_score=40)
    _, _, status, forecast = sr._score_project(linear, issues, 60, 20, [])
    assert status in ("at_risk", "off_track")
    assert forecast == "unowned_assign_now"


# ── Bottom line ───────────────────────────────────────────────────────────────

def test_bottom_line_all_on_track():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    projects = [
        schema.ProjectCard(name="Alpha", owner="A", status="on_track"),
        schema.ProjectCard(name="Beta", owner="B", status="on_track"),
    ]
    line = sr._build_bottom_line(projects, [])
    assert "on track" in line.lower()
    # No decisions needed — the word "decision" may appear but no count > 0
    assert "2 decision" not in line.lower() and "1 decision" not in line.lower()


def test_bottom_line_with_decisions():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    projects = [schema.ProjectCard(name="Alpha", owner="A", status="off_track")]
    decisions = [{"project": "Alpha", "text": "Assign owner"}]
    line = sr._build_bottom_line(projects, decisions)
    assert "decision" in line.lower() or "Alpha" in line


# ── Persistence ───────────────────────────────────────────────────────────────

def test_save_report_creates_files(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")

    report = schema.SteeringReport(
        report_id="steering-2026-05-30",
        generated_at="2026-05-30T08:00:00",
        week_start="2026-05-26",
        week_end="2026-05-30",
        rendered_markdown="# Test",
        rendered_html="<html>Test</html>",
    )

    # Patch config to use tmp_path
    monkeypatch.setattr(sr, "cfg_get", lambda key, default=None: str(tmp_path) if "output_dir" in key else default)

    paths = sr.save_report(report)

    assert paths["json"].exists()
    assert paths["md"].exists()
    assert paths["html"].exists()

    # JSON is valid and loadable
    data = json.loads(paths["json"].read_text())
    assert data["report_id"] == "steering-2026-05-30"

    # Index is created
    index_path = tmp_path / "index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text())
    assert index[0]["id"] == "steering-2026-05-30"


def test_save_report_index_deduplicates(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    monkeypatch.setattr(sr, "cfg_get", lambda key, default=None: str(tmp_path) if "output_dir" in key else default)

    report = schema.SteeringReport(
        report_id="steering-2026-05-30",
        generated_at="2026-05-30T08:00:00",
        week_start="2026-05-26",
        week_end="2026-05-30",
    )

    sr.save_report(report)
    sr.save_report(report)  # second run same week

    index = json.loads((tmp_path / "index.json").read_text())
    ids = [e["id"] for e in index]
    assert ids.count("steering-2026-05-30") == 1


def test_linear_project_health_keeps_projects_with_no_issues(monkeypatch):
    linear = _load("linear_tool_under_test", _ROOT / "tools" / "linear_tool.py")

    def fake_linear_query(query: str, variables: dict = None):
        if "projectMilestones" in query:
            return {
                "data": {
                    "projects": {
                        "nodes": [{
                            "id": "p1",
                            "name": "Compass",
                            "state": "planned",
                            "lead": {"name": "Joao", "email": "joao@example.com"},
                            "targetDate": "2026-06-30",
                            "startDate": "2026-06-01",
                            "projectMilestones": {"nodes": [{"name": "Beta", "targetDate": "2026-06-15"}]},
                        }]
                    }
                }
            }
        return {
            "data": {
                "projects": {
                    "nodes": [{
                        "id": "p1",
                        "issues": {"nodes": []},
                    }]
                }
            }
        }

    monkeypatch.setattr(linear, "linear_query", fake_linear_query)
    result = linear.linear_project_health(days=7)

    assert result["total_projects"] == 1
    project = result["projects"][0]
    assert project["name"] == "Compass"
    assert project["target_date"] == "2026-06-30"
    assert project["start_date"] == "2026-06-01"
    assert project["milestones"][0]["name"] == "Beta"
    assert project["metrics"]["total_issues"] == 0
