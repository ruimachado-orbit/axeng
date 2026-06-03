import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).parents[1] / "axeng"
sys.path.insert(0, str(_ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_weekly_report(config_values: dict[str, str] | None = None):
    config_values = config_values or {}
    fake_config = SimpleNamespace(get=lambda key, default=None: config_values.get(key, default))
    with patch.dict("sys.modules", {
        "config": fake_config,
        "tools.linear_tool": MagicMock(),
        "tools.github_activity": MagicMock(),
        "tools.sprint_health": MagicMock(),
        "tools.dora_metrics": MagicMock(),
        "tools.vacations": MagicMock(),
    }):
        return _load("weekly_report_test_module", _ROOT / "tools" / "weekly_report.py")


def test_weekly_send_report_posts_same_body_to_telegram_and_slack(monkeypatch):
    weekly = _load_weekly_report()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-id")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")

    report_text = "Weekly body\nLine 2"
    telegram_calls = []
    slack_payloads = []

    def fake_run(args, capture_output, text):
        telegram_calls.append(args)
        return SimpleNamespace(returncode=0)

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(req, timeout):
        slack_payloads.append(json.loads(req.data.decode("utf-8")))
        return _Resp()

    with patch("subprocess.run", side_effect=fake_run), patch("urllib.request.urlopen", side_effect=fake_urlopen):
        assert weekly._send_report(report_text, {}) is True

    assert telegram_calls
    assert slack_payloads == [{"text": report_text}]
    telegram_text_args = [arg for arg in telegram_calls[0] if isinstance(arg, str) and arg.startswith("text=")]
    assert telegram_text_args == [f"text={report_text}"]


def test_weekly_send_report_loads_slack_webhook_from_dotenv(tmp_path, monkeypatch):
    weekly = _load_weekly_report()

    env_file = tmp_path / ".env"
    env_file.write_text("SLACK_WEBHOOK_URL=https://hooks.slack.com/services/from-dotenv\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    seen_urls = []

    def fake_urlopen(req, timeout):
        seen_urls.append(req.full_url)
        return _Resp()

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        assert weekly._send_report("Weekly body", {}) is True

    assert seen_urls == ["https://hooks.slack.com/services/from-dotenv"]
