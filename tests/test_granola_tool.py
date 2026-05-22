import importlib.util
import json
from pathlib import Path


def load_granola_module():
    path = Path(__file__).parents[1] / "src" / "tools" / "granola_tool.py"
    spec = importlib.util.spec_from_file_location("granola_tool", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_key_does_not_call_network(monkeypatch):
    granola = load_granola_module()
    monkeypatch.setattr(granola, "load_env", lambda: {})

    result = granola.request_json("/notes")

    assert result["ok"] is False
    assert result["error"] == "MISSING_GRANOLA_API_KEY"
    assert "test-key" not in json.dumps(result)


def test_note_with_transcript_uses_include_param(monkeypatch):
    granola = load_granola_module()
    monkeypatch.setattr(granola, "load_env", lambda: {"GRANOLA_API_KEY": "test-key"})
    seen = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({
                "id": "not_123",
                "title": "Weekly sync",
                "transcript": [{"speaker": "User", "text": "Ship it."}],
            }).encode()

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["auth"] = req.headers.get("Authorization")
        return FakeResponse()

    monkeypatch.setattr(granola.urllib.request, "urlopen", fake_urlopen)

    result = granola.get_note("not_123", include_transcript=True)

    assert result["ok"] is True
    assert "include=transcript" in seen["url"]
    assert seen["auth"] == "Bearer test-key"
    assert result["has_transcript"] is True
    assert result["transcript_items"] == 1


def test_latest_note_fetches_first_visible_note(monkeypatch):
    granola = load_granola_module()
    calls = []

    def fake_list_notes(limit=20, days=None, folder_id=None):
        calls.append((limit, days, folder_id))
        return {"ok": True, "notes": [{"id": "not_latest"}]}

    def fake_get_note(note_id, include_transcript=False):
        return {"ok": True, "tool": "granola_note", "note_id": note_id, "transcript_items": 2}

    monkeypatch.setattr(granola, "list_notes", fake_list_notes)
    monkeypatch.setattr(granola, "get_note", fake_get_note)

    result = granola.latest_note(days=14, include_transcript=True)

    assert calls == [(1, 14, None)]
    assert result["ok"] is True
    assert result["tool"] == "granola_latest"
    assert result["note_id"] == "not_latest"


def test_transcript_text_handles_common_shapes():
    granola = load_granola_module()

    text = granola._text_from_transcript([
        {"speaker": "User", "text": "Hello"},
        {"speaker_name": "Daniel", "content": "World"},
        "raw line",
    ])

    assert "User: Hello" in text
    assert "Daniel: World" in text
    assert "raw line" in text
