"""
Tests for github_issues.py — signal detection and IssueSignals computation.
Run with: pytest tests/test_github_issues.py -v
"""
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).parents[1] / "axeng"
sys.path.insert(0, str(_ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # required for dataclass type resolution in Python 3.14+
    spec.loader.exec_module(mod)
    return mod


# Load schema first so IssueSignals is available
_schema = _load("steering_schema", _ROOT / "tools" / "steering_schema.py")

# Load github_issues with project_map mocked
with patch.dict("sys.modules", {"project_map": MagicMock()}):
    _gi = _load("github_issues", _ROOT / "tools" / "github_issues.py")


# ── Stale detection ───────────────────────────────────────────────────────────

def test_is_stale_old_issue():
    cutoff = datetime.now(timezone.utc) - timedelta(days=_gi.STALE_DAYS)
    old = {"updatedAt": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()}
    assert _gi._is_stale(old, cutoff) is True


def test_is_stale_recent_issue():
    cutoff = datetime.now(timezone.utc) - timedelta(days=_gi.STALE_DAYS)
    recent = {"updatedAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()}
    assert _gi._is_stale(recent, cutoff) is False


def test_is_stale_missing_date():
    cutoff = datetime.now(timezone.utc) - timedelta(days=_gi.STALE_DAYS)
    assert _gi._is_stale({}, cutoff) is True


# ── Unowned detection ─────────────────────────────────────────────────────────

def test_is_unowned_graphql_no_assignees():
    issue = {"assignees": {"nodes": []}}
    assert _gi._is_unowned(issue) is True


def test_is_unowned_graphql_with_assignee():
    issue = {"assignees": {"nodes": [{"login": "alice"}]}}
    assert _gi._is_unowned(issue) is False


def test_is_unowned_rest_empty_list():
    issue = {"assignees": []}
    assert _gi._is_unowned(issue) is True


def test_is_unowned_rest_with_assignee():
    issue = {"assignees": [{"login": "bob"}]}
    assert _gi._is_unowned(issue) is False


# ── Blocked detection ─────────────────────────────────────────────────────────

def test_is_blocked_keyword_in_body():
    issue = {"body": "This is blocked by the auth service.", "comments": {"nodes": []}}
    assert _gi._is_blocked(issue) is True


def test_is_blocked_keyword_in_comment():
    issue = {
        "body": "Normal issue",
        "comments": {"nodes": [{"body": "We are waiting on the infra team"}]},
    }
    assert _gi._is_blocked(issue) is True


def test_is_blocked_no_keywords():
    issue = {"body": "Normal feature request", "comments": {"nodes": []}}
    assert _gi._is_blocked(issue) is False


def test_is_blocked_empty_body():
    issue = {"body": None, "comments": {"nodes": []}}
    assert _gi._is_blocked(issue) is False


# ── Overdue detection ─────────────────────────────────────────────────────────

def test_is_overdue_past_milestone():
    issue = {"milestone": {"dueOn": "2020-01-01"}, "assignees": {"nodes": []}}
    assert _gi._is_overdue(issue, None) is True


def test_is_overdue_future_milestone():
    future = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    issue = {"milestone": {"dueOn": future}}
    assert _gi._is_overdue(issue, None) is False


def test_is_overdue_no_milestone_no_target():
    issue = {"milestone": None}
    assert _gi._is_overdue(issue, None) is False


# ── compute_issue_signals ────────────────────────────────────────────────────

def _make_issue(updated_days_ago=1, has_assignee=True, body="", created_days_ago=10):
    now = datetime.now(timezone.utc)
    return {
        "number": 1,
        "title": "Test issue",
        "updatedAt": (now - timedelta(days=updated_days_ago)).isoformat(),
        "createdAt": (now - timedelta(days=created_days_ago)).isoformat(),
        "assignees": {"nodes": [{"login": "user"}] if has_assignee else []},
        "milestone": None,
        "body": body,
        "comments": {"nodes": []},
        "labels": {"nodes": []},
    }


def test_compute_signals_clean_project():
    raw = {"org/repo": [_make_issue()]}
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals, evidence = _gi.compute_issue_signals(["org/repo"], raw, week_start)
    assert signals.stale_count == 0
    assert signals.unowned_count == 0
    assert signals.blocked_threads == 0
    assert signals.risk_score == 0.0


def test_compute_signals_stale_unowned():
    stale_unowned = _make_issue(updated_days_ago=15, has_assignee=False)
    raw = {"org/repo": [stale_unowned]}
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals, evidence = _gi.compute_issue_signals(["org/repo"], raw, week_start)
    assert signals.stale_count == 1
    assert signals.unowned_count == 1
    assert signals.risk_score > 0


def test_compute_signals_blocked_thread():
    blocked = _make_issue(body="This feature is blocked by the payment API.")
    raw = {"org/repo": [blocked]}
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals, evidence = _gi.compute_issue_signals(["org/repo"], raw, week_start)
    assert signals.blocked_threads == 1
    assert any(e.severity == "critical" for e in evidence)


def test_compute_signals_multiple_repos():
    issue_a = _make_issue(updated_days_ago=12, has_assignee=False)
    issue_b = _make_issue(body="waiting on frontend team")
    raw = {"org/repo-a": [issue_a], "org/repo-b": [issue_b]}
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals, evidence = _gi.compute_issue_signals(
        ["org/repo-a", "org/repo-b"], raw, week_start
    )
    assert signals.stale_count == 1
    assert signals.unowned_count == 1
    assert signals.blocked_threads == 1


def test_compute_signals_empty_repos():
    raw: dict = {}
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals, evidence = _gi.compute_issue_signals([], raw, week_start)
    assert signals.risk_score == 0.0
    assert evidence == []


def test_risk_score_bounded():
    """risk_score must never exceed 100."""
    many_issues = [
        _make_issue(updated_days_ago=20, has_assignee=False, body="blocked by infra")
        for _ in range(20)
    ]
    raw = {"org/repo": many_issues}
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals, _ = _gi.compute_issue_signals(["org/repo"], raw, week_start)
    assert signals.risk_score <= 100.0


# ── GraphQL payload parsing ──────────────────────────────────────────────────

def test_fetch_org_issues_parses_graphql_response(monkeypatch):
    fake_response = {
        "data": {
            "r0": {
                "nameWithOwner": "myorg/frontend",
                "issues": {
                    "nodes": [
                        {
                            "number": 42,
                            "title": "Fix login",
                            "updatedAt": datetime.now(timezone.utc).isoformat(),
                            "createdAt": datetime.now(timezone.utc).isoformat(),
                            "assignees": {"nodes": [{"login": "alice"}]},
                            "milestone": None,
                            "body": "",
                            "comments": {"nodes": []},
                            "labels": {"nodes": []},
                        }
                    ]
                },
            }
        }
    }

    monkeypatch.setattr(_gi, "_gh_graphql", lambda query, variables=None: fake_response)

    result = _gi._fetch_org_issues("myorg", ["frontend"])
    assert "myorg/frontend" in result
    assert len(result["myorg/frontend"]) == 1
    assert result["myorg/frontend"][0]["number"] == 42
