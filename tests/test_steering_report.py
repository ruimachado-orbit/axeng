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


def test_score_transcript_blocker_caps_status():
    """A transcript with an explicit blocker forces the project off on_track,
    regardless of an otherwise-healthy delivery score. (The current model keys
    off concrete blockers, not the softer confidence_tone signal.)"""
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    linear = schema.LinearSignals(completion_rate=80, staleness_rate=5, velocity=2.0)
    issues = schema.IssueSignals(risk_score=5)
    blocked = schema.TranscriptSignal(
        note_id="n1", title="Urgent meeting", note_date="2026-05-28",
        blockers=["Waiting on vendor SDK access"],
        confidence_tone="urgent",
    )
    score, confidence, status, forecast = sr._score_project(linear, issues, 50, 80, [blocked])
    assert status in ("at_risk", "off_track")
    assert forecast == "blocked_needs_escalation"


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
    assert score_declining == score_stable - 5
    assert score_improving == score_stable + 3


def test_score_declining_velocity_can_flip_status():
    """A borderline on_track project should drop to at_risk if velocity is declining."""
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    # on_track requires health_score >= 70. Pick inputs that land just inside
    # the on_track band with stable velocity so the −5 declining modifier crosses
    # the boundary back into at_risk.
    linear = schema.LinearSignals(
        completion_rate=57, staleness_rate=15, velocity=0.5,
        todo=6, in_progress=2, completed=2,
    )
    issues = schema.IssueSignals(risk_score=8)

    score_stable, _, status_stable, _ = sr._score_project(linear, issues, 70, 57, [], velocity_trend="stable")
    score_declining, _, status_declining, _ = sr._score_project(linear, issues, 70, 57, [], velocity_trend="declining")

    # Verify the stable score sits in the narrow flip window [70, 75) before asserting
    assert 70 <= score_stable < 75, f"Test setup issue: stable score {score_stable} not in [70,75)"
    assert score_declining < 70

    assert status_stable == "on_track"
    assert status_declining == "at_risk"


def test_score_overdue_incomplete_project_is_off_track_with_low_confidence():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report_overdue_status", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema_overdue_status", _ROOT / "tools" / "steering_schema.py")
    linear = schema.LinearSignals(
        completion_rate=80, staleness_rate=0, velocity=2.0,
        todo=2, in_progress=1, completed=5,
    )
    issues = schema.IssueSignals(risk_score=5)
    commits = schema.CommitSignals(commits_this_week=12)

    score, confidence, status, forecast = sr._score_project(
        linear, issues, 90, 70, [], commit_signals=commits, days_left=-5
    )

    assert score <= 44
    assert status == "off_track"
    assert confidence == "low"
    assert forecast == "target_date_at_risk"


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


# ── Goal-oriented synthesis ───────────────────────────────────────────────────

def _sr_and_schema():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report", _ROOT / "tools" / "steering_report.py")
    schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")
    return sr, schema


def test_goal_progress_frames_against_milestone():
    """goal_progress should lead with the current milestone and scope %, not commits."""
    sr, schema = _sr_and_schema()
    card = schema.ProjectCard(
        name="Starfleet", owner="Ana",
        objective="Ship a multi-tenant API gateway.",
        work_progress_pct=62, time_progress_pct=80, days_left=21, target_date="2099-06-24",
        milestones=[
            {"name": "Auth", "target_date": "2000-01-01", "progress_pct": 100.0},
            {"name": "Routing", "target_date": "2099-06-10", "progress_pct": 40.0},
            {"name": "GA", "target_date": "2099-06-24", "progress_pct": 0.0},
        ],
        linear_signals=schema.LinearSignals(completion_rate=62, velocity=0.5),
    )
    gp = sr._build_goal_progress(card)
    assert gp is not None
    # Current milestone is the earliest *upcoming* one
    assert card.current_milestone["name"] == "Routing"
    assert "Routing" in gp
    assert "%" in gp                      # scope progress is surfaced
    assert "trailing schedule" in gp      # work(62) far behind time(80)


def test_goal_progress_handles_no_milestones():
    """With no milestones, fall back to scope vs time without crashing."""
    sr, schema = _sr_and_schema()
    card = schema.ProjectCard(
        name="Brain", owner="Rui",
        work_progress_pct=30, time_progress_pct=30, days_left=60,
        linear_signals=schema.LinearSignals(completion_rate=30),
    )
    gp = sr._build_goal_progress(card)
    assert gp is not None
    assert "30%" in gp
    assert card.current_milestone is None


def test_delivered_bullets_group_related_artifact_lists():
    sr, schema = _sr_and_schema()
    card = schema.ProjectCard(
        name="Constellation v2",
        owner="Pedro",
        milestones=[{"name": "Portal MVP", "target_date": "2099-06-30"}],
        linear_signals=schema.LinearSignals(
            recently_completed_titles=[
                "OPS-1 — Offboarding QA: Jira",
                "OPS-2 — Offboarding QA: Slack",
                "OPS-3 — Offboarding QA: WhatsApp",
                "OPS-4 — Offboarding QA: Microsoft 365",
            ]
        ),
    )

    bullets = sr._build_delivered_bullets(card)

    assert any("Expanded Offboarding QA coverage across" in b for b in bullets)
    assert not any("Offboarding QA: Jira" == b.rstrip(".") for b in bullets)


def test_week_delta_is_milestone_oriented_not_duplicate_delivery_text():
    sr, schema = _sr_and_schema()
    card = schema.ProjectCard(
        name="Heimdall",
        owner="Ricardo",
        milestones=[{"name": "v1.x current operations", "target_date": "2099-06-15"}],
        linear_signals=schema.LinearSignals(recently_completed_titles=["OPS-1 — Silent failure handling"]),
    )

    delivered = sr._build_delivered_bullets(card)
    week_delta = sr._build_week_delta(card)

    assert delivered
    assert week_delta == "Advanced v1.x current operations through this week's delivered work."
    assert week_delta != delivered[0]


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


def test_bottom_line_prioritises_velocity_and_nearest_milestone():
    sr, schema = _sr_and_schema()
    projects = [
        schema.ProjectCard(
            name="Adam",
            owner="A",
            status="at_risk",
            days_left=27,
            health_score=45,
            linear_signals=schema.LinearSignals(velocity=0, todo=5, in_progress=5),
            milestones=[{"name": "Stable v1", "target_date": "2099-06-30"}],
        ),
        schema.ProjectCard(
            name="Heimdall",
            owner="B",
            status="at_risk",
            days_left=12,
            health_score=60,
            linear_signals=schema.LinearSignals(velocity=0, todo=7, in_progress=4),
            milestones=[{"name": "v1.x current operations", "target_date": "2099-06-15"}],
        ),
    ]

    line = sr._build_bottom_line(projects, [])

    assert "no measurable delivery velocity" in line.lower()
    assert "Heimdall" in line
    assert "12d" in line


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


def test_send_report_uses_slack_webhook_env_fallback(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report_send_slack", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema_send_slack", _ROOT / "tools" / "steering_schema.py")
    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(top_risk="Portfolio risk summary."),
    )
    paths = {"html": tmp_path / "report.html"}
    paths["html"].write_text("<html></html>")

    monkeypatch.setattr(sr, "cfg_get", lambda key, default=None: None)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_response
    mock_context.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_context) as mock_urlopen:
        delivered = sr.send_report(report, paths)

    assert delivered is True
    mock_urlopen.assert_called_once()


def test_send_report_prefers_slack_webhook_env_over_config(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report_send_slack_precedence", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema_send_slack_precedence", _ROOT / "tools" / "steering_schema.py")
    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(top_risk="Portfolio risk summary."),
    )
    paths = {"html": tmp_path / "report.html"}
    paths["html"].write_text("<html></html>")

    def fake_cfg_get(key, default=None):
        values = {
            "steering.webhook_url": "https://hooks.slack.com/services/from-config",
            "reporting.webhook_url": None,
        }
        return values.get(key, default)

    monkeypatch.setattr(sr, "cfg_get", fake_cfg_get)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/from-env")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_response
    mock_context.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_context) as mock_urlopen:
        delivered = sr.send_report(report, paths)

    assert delivered is True
    req = mock_urlopen.call_args[0][0]
    assert req.full_url == "https://hooks.slack.com/services/from-env"


def test_send_report_slack_payload_includes_summary_and_attention_projects(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report_send_slack_payload", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema_send_slack_payload", _ROOT / "tools" / "steering_schema.py")
    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=3,
            on_track=1,
            at_risk=2,
            off_track=0,
            decisions_needed=1,
            top_risk="Multiple strategic initiatives are showing insufficient delivery momentum.",
        ),
        projects=[
            schema.ProjectCard(
                name="Adam",
                owner="Rui",
                status="at_risk",
                days_left=27,
                target_date="2099-06-30",
                milestones=[{"name": "Stable v1", "target_date": "2099-06-30"}],
                delivered_bullets=["No delivery evidence this week"],
                planned_bullets=["Stabilise Adam v1 runtime and interfaces"],
            ),
            schema.ProjectCard(
                name="Heimdall",
                owner="Ricardo",
                status="at_risk",
                days_left=12,
                target_date="2099-06-15",
                milestones=[{"name": "v1.x current operations", "target_date": "2099-06-15"}],
                delivered_bullets=["Advanced operational hardening work"],
                planned_bullets=["Resolve silent failures and SPOFs"],
            ),
            schema.ProjectCard(
                name="Auria",
                owner="Diogo",
                status="on_track",
                delivered_bullets=["Delivered new mobile session states"],
                milestones=[{"name": "Build complete", "target_date": "2099-06-20"}],
            ),
        ],
        client_summary=(
            "§Delivered\n"
            "Constellation v2: Completed offboarding QA for four platforms\n"
            "Auria: Delivered new mobile session states and UI improvements\n\n"
            "§Committed Next\n"
            "Adam: Stabilise Adam v1 runtime and interfaces\n"
            "Heimdall: Resolve silent failures and SPOFs\n\n"
            "§Risks\n"
            "Adam: No measurable delivery progress this week against Stable v1"
        ),
        decisions_needed=[{"project": "Heimdall", "text": "Decide whether to narrow scope for June milestone."}],
    )
    paths = {"html": tmp_path / "report.html"}
    paths["html"].write_text("<html></html>")

    monkeypatch.setattr(sr, "cfg_get", lambda key, default=None: None)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/from-env")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_response
    mock_context.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_context) as mock_urlopen:
        delivered = sr.send_report(report, paths)

    assert delivered is True
    req = mock_urlopen.call_args[0][0]
    payload = json.loads(req.data.decode("utf-8"))
    blocks_text = json.dumps(payload["blocks"])
    assert "Portfolio Health" in blocks_text
    assert "Projects by severity" in blocks_text
    assert "Delivered This Week" in blocks_text
    assert "Committed Next Week" in blocks_text
    assert "Project Detail" in blocks_text
    assert "On Track" in blocks_text
    assert "Adam" in blocks_text
    assert "Heimdall" in blocks_text
    assert "Milestone Radar" in blocks_text


def test_send_report_loads_slack_webhook_from_dotenv(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report_send_slack_dotenv", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema_send_slack_dotenv", _ROOT / "tools" / "steering_schema.py")
    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(top_risk="Portfolio risk summary."),
    )
    paths = {"html": tmp_path / "report.html"}
    paths["html"].write_text("<html></html>")

    env_file = tmp_path / ".env"
    env_file.write_text("SLACK_WEBHOOK_URL=https://hooks.slack.com/services/from-dotenv\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sr, "cfg_get", lambda key, default=None: None)
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    mock_response = MagicMock()
    mock_response.status = 200
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_response
    mock_context.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_context) as mock_urlopen:
        delivered = sr.send_report(report, paths)

    assert delivered is True
    mock_urlopen.assert_called_once()


def test_send_report_passes_steering_from_to_gmail(tmp_path, monkeypatch):
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report_send_from", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema_send_from", _ROOT / "tools" / "steering_schema.py")
    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
    )
    gmail_script = tmp_path / "google_api.py"
    gmail_script.write_text("#!/usr/bin/env python3\n")
    html_path = tmp_path / "report.html"
    html_path.write_text("<html></html>")
    paths = {"html": html_path}

    def fake_cfg_get(key, default=None):
        values = {
            "steering.recipients": ["ceo@example.com"],
            "steering.from": "axeng@example.com",
            "email.gmail_script": str(gmail_script),
        }
        return values.get(key, default)

    monkeypatch.setattr(sr, "cfg_get", fake_cfg_get)

    completed = MagicMock()
    completed.returncode = 0
    completed.stderr = ""
    with patch("subprocess.run", return_value=completed) as mock_run:
        delivered = sr.send_report(report, paths)

    assert delivered is True
    cmd = mock_run.call_args[0][0]
    assert "--from" in cmd
    assert "axeng@example.com" in cmd


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


def test_render_markdown_includes_portfolio_health_summary():
    schema = _load("steering_schema_render_md", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_render_md", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=4,
            on_track=1,
            at_risk=2,
            off_track=0,
            inactive=1,
            decisions_needed=1,
            top_risk="One project needs intervention.",
        ),
    )

    md = render.render_markdown(report)

    assert "## Portfolio Health" in md
    assert "- On Track: 1" in md
    assert "- Need Attention: 2" in md
    assert "- Inactive: 1" in md


def test_render_html_project_card_header_is_compact():
    schema = _load("steering_schema_render_html", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_render_html", _ROOT / "tools" / "steering_render.py")

    project = {
        "name": "Heimdall",
        "owner": "Ricardo Mendes",
        "status": "at_risk",
        "health_score": 60,
        "score_trend": {"display": "", "movement": "flat"},
        "work_progress_pct": 20,
        "time_progress_pct": 35,
        "target_date": "2026-06-15",
        "days_left": 12,
        "milestones": [{"name": "v1.x current operations", "target_date": "2026-06-15", "progress_pct": 20.0}],
        "current_milestone": {"name": "v1.x current operations", "target_date": "2026-06-15", "progress_pct": 20.0},
        "health_signals": ["No velocity — 11 issues unstarted or stalled"],
        "blockers": [],
        "confidence": "medium",
        "next_week": "Deliver Critical: silent failures and SPOFs.",
        "planned_bullets": ["Deliver High: observability gaps."],
        "delivered_bullets": ["Closed silent failure path in runtime"],
    }

    html = render._html_project_card(project, "stable", render._brand())

    assert "Project Card" not in html
    assert "Heimdall" in html
    assert "Ricardo Mendes" in html
    assert "60/100" in html
    assert "At Risk · Act Now" in html
    assert "Milestone" in html
    assert "Progress" in html
    assert "20% complete · 12d remaining" in html
    assert "color:#d97706;font-weight:700;line-height:1.45;\">20% complete · 12d remaining" in html
    assert "This Week" in html
    assert "Closed silent failure path in runtime" in html


def test_render_html_project_card_uses_target_date_when_no_named_milestone():
    render = _load("steering_render_target_date_fallback", _ROOT / "tools" / "steering_render.py")

    project = {
        "name": "Starfleet Gateway",
        "owner": "Ricardo Mendes",
        "status": "off_track",
        "health_score": 44,
        "score_trend": {"display": "", "movement": "flat"},
        "work_progress_pct": 76,
        "time_progress_pct": 100,
        "target_date": "2026-05-31",
        "days_left": -3,
        "milestones": [],
        "current_milestone": None,
        "health_signals": ["The current target date passed 3d ago with only 76% complete"],
        "blockers": [],
        "confidence": "low",
    }

    html = render._html_project_card(project, "stable", render._brand())

    assert "Target date — 2026-05-31" in html
    assert "76% complete · 3d overdue" in html
    assert "No milestone set" not in html


def test_build_status_explanation_uses_target_date_fallback_without_milestone():
    with patch.dict("sys.modules", {
        "tools.github_issues": MagicMock(),
        "tools.steering_granola": MagicMock(),
        "tools.steering_render": MagicMock(),
    }):
        sr = _load("steering_report_reason_target_date_fallback", _ROOT / "tools" / "steering_report.py")

    schema = _load("steering_schema_reason_target_date_fallback", _ROOT / "tools" / "steering_schema.py")
    card = schema.ProjectCard(
        name="Starfleet Gateway",
        owner="Ricardo Mendes",
        status="off_track",
        work_progress_pct=76,
        time_progress_pct=100,
        days_left=-3,
        target_date="2026-05-31",
        milestones=[],
        linear_signals=schema.LinearSignals(todo=3, in_progress=1, velocity=0),
    )

    reasons = sr._build_status_explanation(card)

    assert "The current target date passed 3d ago with only 76% complete" in reasons
    assert not any("current milestone is past its target date" in reason for reason in reasons)


def test_render_html_restores_portfolio_health_narrative():
    schema = _load("steering_schema_portfolio_health", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_portfolio_health", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=3,
            on_track=1,
            at_risk=2,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="Two projects need intervention.",
            portfolio_risks=["1 project has stale work >7 days"],
        ),
        projects=[
            schema.ProjectCard(
                name="Brain",
                owner="A",
                status="at_risk",
                health_signals=["No velocity — 4 issues unstarted or stalled"],
            ),
            schema.ProjectCard(
                name="Starfleet Gateway",
                owner="B",
                status="at_risk",
                days_left=-3,
                health_signals=["Milestone overdue: 'Beta' was due 2026-06-01"],
            ),
            schema.ProjectCard(
                name="Maio Workspace",
                owner="C",
                status="on_track",
            ),
        ],
    )

    html = render.render_html(report)

    assert "Portfolio Health: <span style=\"color:#d97706;\">At Risk</span>" in html
    assert "CRITICAL" in html
    assert "WARNING" in html
    assert "POSITIVE" in html
    assert "<strong>Brain</strong> has no delivery velocity." in html
    assert "<strong>Starfleet Gateway</strong> milestone missed — 3d past deadline." in html
    assert "<strong>Maio Workspace</strong> progressing as planned." in html


def test_render_html_portfolio_table_includes_explicit_trend_column():
    schema = _load("steering_schema_trend_table", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_trend_table", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=1,
            on_track=0,
            at_risk=1,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="One project is slipping.",
        ),
        projects=[
            schema.ProjectCard(
                name="Adam",
                owner="Rui",
                status="at_risk",
                health_score=45,
                confidence="medium",
                target_date="2026-06-30",
                score_trend=schema.ScoreTrend(previous_score=52, score=45, delta=-7, movement="down", display="↓7"),
                milestones=[{"name": "Stable v1", "target_date": "2026-06-30"}],
            ),
        ],
    )

    html = render.render_html(report)

    assert ">Trend</td>" in html
    assert "↑" not in html
    assert "↓ 7" in html


def test_render_html_portfolio_table_confidence_uses_status_color():
    schema = _load("steering_schema_confidence_color", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_confidence_color", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=1,
            on_track=0,
            at_risk=1,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="One project is slipping.",
        ),
        projects=[
            schema.ProjectCard(
                name="Adam",
                owner="Rui",
                status="at_risk",
                health_score=45,
                confidence="medium",
                target_date="2026-06-30",
                milestones=[{"name": "Stable v1", "target_date": "2026-06-30"}],
            ),
        ],
    )

    html = render.render_html(report)

    assert 'font-size:12px;font-weight:700;color:#d97706;">Medium</td>' in html
    assert '>2026-06-30</td>' in html
    assert '2026-06-30<span' not in html


def test_render_html_portfolio_table_confidence_color_depends_on_confidence_not_status():
    schema = _load("steering_schema_confidence_consistent", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_confidence_consistent", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=3,
            on_track=1,
            at_risk=2,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="Mixed portfolio confidence.",
        ),
        projects=[
            schema.ProjectCard(name="Adam", owner="Rui", status="at_risk", confidence="medium", health_score=45),
            schema.ProjectCard(name="Gateway", owner="Rui", status="on_track", confidence="medium", health_score=70),
            schema.ProjectCard(name="Workspace", owner="Diogo", status="on_track", confidence="high", health_score=84),
        ],
    )

    html = render.render_html(report)

    assert html.count('color:#d97706;">Medium</td>') == 2
    assert 'color:#16a34a;">High</td>' in html


def test_render_html_omits_portfolio_recap_sections():
    schema = _load("steering_schema_render_omit_recaps", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_omit_recaps", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=1,
            on_track=1,
            at_risk=0,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="Portfolio is on track.",
        ),
        projects=[
            schema.ProjectCard(
                name="Auria",
                owner="Rui",
                status="on_track",
                health_score=82,
            ),
        ],
        this_week_summary=["Auria shipped live session UI states."],
        next_week_summary=["Auria to finish one in-progress issue."],
        client_summary="§Delivered\nAuria shipped live session UI states.\n\n§Committed Next\nAuria to finish one in-progress issue.",
    )

    html = render.render_html(report)

    assert "Delivered This Week" not in html
    assert ">Next<" not in html
    assert "Weekly Summary" not in html
    assert "Inactive Projects" not in html
    assert "Portfolio Risks" not in html


def test_render_html_on_track_projects_use_same_detail_layout():
    schema = _load("steering_schema_on_track_layout", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_on_track_layout", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=1,
            on_track=1,
            at_risk=0,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="Portfolio is on track.",
        ),
        projects=[
            schema.ProjectCard(
                name="Auria",
                owner="Rui",
                status="on_track",
                health_score=82,
                confidence="high",
                work_progress_pct=65,
                days_left=14,
                target_date="2026-06-20",
                milestones=[{"name": "Mobile polish", "target_date": "2026-06-20"}],
                delivered_bullets=["Shipped live session audio states"],
                planned_bullets=["Finish mobile settings flow"],
                next_week="Finish mobile settings flow.",
            ),
        ],
    )

    html = render.render_html(report)

    assert "Project Detail" in html
    assert "On Track" in html
    assert "This Week" in html
    assert "Next Week" in html
    assert "Shipped live session audio states" in html


def test_render_html_decisions_block_dedupes_projects_already_in_detail_cards():
    schema = _load("steering_schema_decision_dedupe", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_decision_dedupe", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=1,
            on_track=0,
            at_risk=0,
            off_track=1,
            inactive=0,
            decisions_needed=1,
            top_risk="Starfleet Gateway needs a scope decision.",
        ),
        projects=[
            schema.ProjectCard(
                name="Starfleet Gateway",
                owner="Ricardo Mendes",
                status="off_track",
                health_score=44,
                confidence="low",
                work_progress_pct=76,
                target_date="2026-05-31",
                days_left=-3,
                decision_needed="Decide: rescope Starfleet Gateway or accept date slip.",
            ),
        ],
        decisions_needed=[
            {
                "project": "Starfleet Gateway",
                "owner": "Ricardo Mendes",
                "text": "Decide: rescope Starfleet Gateway or accept date slip.",
                "status": "off_track",
            }
        ],
    )

    html = render.render_html(report)

    assert "Decisions Needed — 1" in html
    assert "Action required this week" not in html
    assert "Decide: rescope Starfleet Gateway or accept date slip." in html


def test_render_html_stat_cards_have_fixed_height():
    schema = _load("steering_schema_stat_height", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_stat_height", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=2,
            on_track=1,
            at_risk=1,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="One project is slipping.",
        ),
        projects=[
            schema.ProjectCard(name="Auria", owner="Rui", status="on_track"),
            schema.ProjectCard(name="Adam", owner="Rui", status="at_risk"),
        ],
    )

    html = render.render_html(report)

    assert "height:116px;" in html


def test_render_html_header_has_no_recipient_and_footer_has_no_signals_line():
    schema = _load("steering_schema_header_footer_cleanup", _ROOT / "tools" / "steering_schema.py")
    render = _load("steering_render_header_footer_cleanup", _ROOT / "tools" / "steering_render.py")

    report = schema.SteeringReport(
        report_id="steering-2026-06-03",
        generated_at="2026-06-03T09:00:00",
        week_start="2026-06-01",
        week_end="2026-06-05",
        portfolio_summary=schema.PortfolioSummary(
            total_projects=1,
            on_track=1,
            at_risk=0,
            off_track=0,
            inactive=0,
            decisions_needed=0,
            top_risk="Portfolio is on track.",
        ),
        projects=[schema.ProjectCard(name="Auria", owner="Rui", status="on_track")],
        sources=["linear", "github_issues"],
        errors=["partial data"],
    )

    html = render.render_html(report)

    assert "For Recipient" not in html
    assert "Signals:" not in html
    assert "partial data" not in html
