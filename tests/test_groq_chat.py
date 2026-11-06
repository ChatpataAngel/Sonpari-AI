import json
from io import BytesIO
from urllib.error import HTTPError

from aiko.groq_chat import GroqChat, _clean_external_text


def test_groq_is_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_ENABLED", "true")
    client = GroqChat()
    assert not client.enabled
    assert client.reply("tell me something", "hinglish", {}) is None


def test_groq_can_be_disabled_even_with_api_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "dummy-test-key")
    monkeypatch.setenv("GROQ_ENABLED", "false")
    assert not GroqChat().enabled


def test_external_text_redacts_obvious_secrets_and_contact_details():
    source = "api_key=supersecret mail me at example@test.com call +91 98765 43210"
    cleaned = _clean_external_text(source)
    assert "supersecret" not in cleaned
    assert "example@test.com" not in cleaned
    assert "98765 43210" not in cleaned
    assert "[private detail removed]" in cleaned


def test_reply_uses_groq_chat_completions_and_recent_context(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "areyyy baby, that sounds fun 😭💗"}}]
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("aiko.groq_chat.urlopen", fake_urlopen)
    client = GroqChat(api_key="dummy-test-key", model="openai/gpt-oss-20b", enabled=True)
    response = client.reply(
        "I finally finished my project!",
        "hinglish",
        {"name": "Bhawna", "age": 21, "backstory": "fictional college student", "personality_traits": ["playful"]},
        [
            {"role": "user", "text": "i was stuck all day"},
            {"role": "assistant", "text": "kya issue aa raha tha baby?"},
        ],
    )

    assert response == "areyyy baby, that sounds fun 😭💗"
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"].get("Authorization") == "Bearer dummy-test-key"
    assert captured["headers"].get("User-agent", "").startswith("AikoBot/24")
    assert captured["headers"].get("Accept") == "application/json"
    assert captured["payload"]["model"] == "openai/gpt-oss-20b"
    assert captured["payload"]["messages"][-1] == {
        "role": "user", "content": "I finally finished my project!"
    }
    assert any(m["content"] == "i was stuck all day" for m in captured["payload"]["messages"])
    assert captured["timeout"] <= 30


def test_reply_returns_none_for_empty_and_command_messages(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "dummy-test-key")
    monkeypatch.setenv("GROQ_ENABLED", "true")
    client = GroqChat()
    assert client.reply("   ", "hinglish", {}) is None
    assert client.reply("/search private stuff", "hinglish", {}) is None


def test_http_error_logs_sanitized_provider_reason(monkeypatch, caplog):
    from aiko.groq_chat import GroqChat

    error_body = json.dumps({"error": {
        "message": "The model openai/gpt-oss-20b is blocked at the project level.",
        "type": "permissions_error",
        "code": "model_permission_blocked_project",
    }}).encode("utf-8")

    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 403, "Forbidden", {}, BytesIO(error_body))

    monkeypatch.setattr("aiko.groq_chat.urlopen", fake_urlopen)
    client = GroqChat(api_key="dummy-test-key", model="openai/gpt-oss-20b", enabled=True)
    result = client.reply("tell me something", "hinglish", {})

    assert result is None
    assert "HTTP 403" in caplog.text
    assert "model_permission_blocked_project" in caplog.text
    assert "blocked at the project level" in caplog.text
    assert "dummy-test-key" not in caplog.text


def test_cloudflare_1010_error_is_logged_as_edge_block_not_model_permission(monkeypatch, caplog):
    error_body = json.dumps({
        "code": 1010,
        "type": "https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/",
        "message": "The site owner has blocked access based on your browser's signature.",
    }).encode("utf-8")

    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 403, "Forbidden", {}, BytesIO(error_body))

    monkeypatch.setattr("aiko.groq_chat.urlopen", fake_urlopen)
    client = GroqChat(api_key="dummy-test-key", model="openai/gpt-oss-20b", enabled=True)
    assert client.reply("tell me something", "hinglish", {}) is None
    assert "cloudflare_code=1010" in caplog.text
    assert "browser's signature" in caplog.text
    assert "dummy-test-key" not in caplog.text


def test_bare_generic_model_refusal_is_not_sent_as_a_chat_reply(monkeypatch, caplog):
    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "I'm sorry, but I can't help with that."}}]
            }).encode("utf-8")

    import logging
    caplog.set_level(logging.INFO)
    monkeypatch.setattr("aiko.groq_chat.urlopen", lambda request, timeout: FakeResponse())
    client = GroqChat(api_key="dummy-test-key", model="openai/gpt-oss-20b", enabled=True)
    assert client.reply("a mild flirty joke", "hinglish", {"name": "Bhawna", "age": 21}) is None
    assert "keeping local dialogue reply" in caplog.text
    assert "dummy-test-key" not in caplog.text

