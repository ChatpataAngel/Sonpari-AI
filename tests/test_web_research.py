import sys
import re
from types import SimpleNamespace

import pytest

from aiko.web_research import WebResearcher, WebSearchUnavailable


@pytest.fixture(autouse=True)
def prevent_real_provider_requests(monkeypatch):
    """Unit tests use mocked providers and never call live search services."""
    monkeypatch.setattr("aiko.web_research.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("network disabled in tests")))
    monkeypatch.setenv("AIKO_SEARXNG_URL", "")
    monkeypatch.delenv("AIKO_ENABLE_DDG_HTML_FALLBACK", raising=False)


def test_auto_mode_detects_research_prompts_but_not_chit_chat():
    assert WebResearcher.should_search("What is Python 3.14?", "auto")
    assert WebResearcher.should_search("explain how a Telegram bot works", "auto")
    assert WebResearcher.should_search("Mujhe Python ka error fix karna hai", "auto")
    assert WebResearcher.should_search("I love you baby 😘", "auto")
    assert WebResearcher.should_search("i lobe you", "auto")
    assert not WebResearcher.should_search("Kya kar rahi ho?", "auto")


def test_hinglish_wellbeing_checkins_never_trigger_web_even_in_always_mode():
    # These were falling into the generic web reply composer after /web always.
    for prompt in (
        "Kese ho babyy 😚😚💋",
        "Kese ho baby?",
        "Aap kese ho me to acha hu 💋😋",
        "kaisi ho jaan",
        "Tum kaise ho?",
    ):
        assert WebResearcher.is_local_conversation_control(prompt), prompt
        assert not WebResearcher.should_search(prompt, "always"), prompt
        assert not WebResearcher.should_search(prompt, "auto"), prompt


def test_modes_and_explicit_search_override(tmp_path):
    path = tmp_path / "web_preferences.json"
    web = WebResearcher(path)
    assert web.get_mode(123) == "auto"
    assert web.set_mode(123, "off")
    assert not WebResearcher.should_search("What is Python?", web.get_mode(123))
    assert WebResearcher.should_search("search: What is Python?", web.get_mode(123))
    restored = WebResearcher(path)
    assert restored.get_mode(123) == "off"
    assert not restored.set_mode(123, "nope")


def test_keywords_include_subject_terms():
    query = WebResearcher.keywords("Can you explain how to fix a Python Telegram bot import error?")
    assert "python" in query
    assert "telegram" in query
    assert "import" in query
    assert "error" in query


def test_answer_searches_full_prompt_and_keywords_and_formats_next_action(monkeypatch):
    calls = []

    class FakeDDGS:
        def text(self, query, **kwargs):
            calls.append(query)
            if len(calls) == 1:
                return [
                    {"title": f"Python docs {i}", "href": f"https://example.com/python-{i}", "body": "Official Python documentation."}
                    for i in range(6)
                ]
            return [{"title": "Telegram bot guide", "href": "https://example.com/bot", "body": "Steps for bot setup."}]

    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=FakeDDGS))
    prompt = "How do I set up a Python Telegram bot?"
    monkeypatch.setattr(WebResearcher, "_search_html", lambda self, query, limit: [])
    answer = WebResearcher().answer(prompt, "hinglish")
    assert calls[0] == prompt
    assert "python telegram bot" in calls[1]
    assert all(not re.search(r"\b(?:kya|kaise|kaun|kon|hai|hain|mujhe|tumse|pyaar)\b", q, re.I) for q in calls)
    assert "poora sawaal" in answer.lower()
    assert "concise answer" in answer.lower()
    assert "https://example.com/python-0" in answer
    assert "https://example.com/python-1" in answer
    assert "https://example.com/bot" in answer
    assert len(calls) == 2  # keyword search still runs when the first query is rich


def test_missing_ddgs_has_helpful_error(monkeypatch):
    monkeypatch.setenv("AIKO_ENABLE_DDG_HTML_FALLBACK", "true")
    monkeypatch.delitem(sys.modules, "ddgs", raising=False)
    # Force the import itself to fail even if a system package happens to exist.
    import builtins
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "ddgs":
            raise ImportError("blocked by test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    monkeypatch.setattr(WebResearcher, "_search_html", lambda self, query, limit: (_ for _ in ()).throw(TimeoutError("offline")))
    with pytest.raises(WebSearchUnavailable, match="connect to a provider"):
        WebResearcher().search("What is Python?")


def test_response_expansion_loader_accepts_flat_list_and_goodnight_alias():
    from aiko.dialogue_rules import apply_response_expansions

    pools = {"hinglish": [], "hi": [], "en": []}
    rules = [("goodnight", None, pools)]
    apply_response_expansions(rules, {"good_night": ["so jao ji", "sweet dreams"]})
    assert pools["hinglish"] == ["so jao ji", "sweet dreams"]
    assert pools["hi"] == []


def test_response_expansion_loader_accepts_language_map():
    from aiko.dialogue_rules import apply_response_expansions

    pools = {"hinglish": [], "hi": [], "en": []}
    rules = [("greeting", None, pools)]
    apply_response_expansions(rules, {"greeting": {"en": ["hello there"], "hinglish": "hii ji"}})
    assert pools["en"] == ["hello there"]
    assert pools["hinglish"] == ["hii ji"]


def test_answer_is_transparent_when_no_results(monkeypatch):
    class EmptyDDGS:
        def text(self, query, **kwargs):
            return []

    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=EmptyDDGS))
    monkeypatch.setattr(WebResearcher, "_search_html", lambda self, query, limit: [])
    answer = WebResearcher().answer("What is a fictional obscure term?", "en")
    assert "no useful results" in answer.lower()
    assert "shorter keyword" in answer.lower()


def test_hinglish_who_questions_and_shakespeare_spellings_are_detected():
    assert WebResearcher.should_search("ye shakespear kon h", "auto")
    assert WebResearcher.should_search("kon h ye shakespear", "auto")
    assert WebResearcher.should_search("kon hai Shakespeare", "auto")
    assert WebResearcher.keywords("ye shakespear kon h") == "shakespeare"


def test_builtin_html_fallback_can_run_without_ddgs(monkeypatch):
    monkeypatch.setenv("AIKO_ENABLE_DDG_HTML_FALLBACK", "true")
    import builtins
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "ddgs":
            raise ImportError("blocked by test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    monkeypatch.setattr(WebResearcher, "_search_html", lambda self, query, limit: [
        {"title": "William Shakespeare", "url": "https://example.com/shakespeare", "body": "English playwright and poet."}
    ])
    result = WebResearcher().search("ye shakespear kon h")
    assert result and result[0]["title"] == "William Shakespeare"


def test_love_prompt_searches_reply_inspiration_and_returns_one_girlfriend_reply(monkeypatch):
    calls = []

    class FakeDDGS:
        def text(self, query, **kwargs):
            calls.append(query)
            if "girlfriend replies" in query:
                return [{
                    "title": "Funny and playful ways to reply to I love you",
                    "href": "https://example.com/love-replies",
                    "body": "Cute, funny and playful affectionate text message ideas.",
                }]
            return [{
                "title": "I Love You meaning",
                "href": "https://example.com/love",
                "body": "A common expression of affection.",
            }]

    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=FakeDDGS))
    monkeypatch.setattr(WebResearcher, "_search_html", lambda self, query, limit: [])
    answer = WebResearcher().answer("I love you", "hinglish")
    assert "English examples" in calls[0]
    assert "girlfriend replies" in calls[1]
    assert any(emoji in answer for emoji in ("💗", "❤️", "💕", "😘", "💋"))
    assert "https://example.com" not in answer
    assert not answer.startswith("haan ji, maine tumhara poora prompt")


def test_romantic_and_supportive_messages_auto_search_for_reply_ideas():
    for prompt in ("I love you", "I miss you", "you are so cute", "I feel lonely", "I got promoted"):
        assert WebResearcher.should_search(prompt, "auto"), prompt


def test_girlfriend_reply_falls_back_locally_when_web_search_is_unavailable(monkeypatch):
    monkeypatch.setattr(WebResearcher, "search", lambda self, prompt, **kwargs: (_ for _ in ()).throw(WebSearchUnavailable("offline")))
    answer = WebResearcher().answer("I love you", "en")
    assert answer
    assert "💗" in answer or "❤️" in answer or "💕" in answer
    assert "unavailable" not in answer.lower()


def test_hinglish_questions_are_rewritten_to_english_search_queries():
    queries = WebResearcher._queries_for_prompt("ye shakespear kon h")
    assert queries[0] == "Who is shakespeare?"
    assert all("kon" not in q.casefold() and "hai" not in q.casefold() for q in queries)
    assert all(re.search(r"[\u0900-\u097f]", q) is None for q in queries)


def test_hinglish_romantic_prompt_search_queries_are_english():
    queries = WebResearcher._queries_for_prompt("mujhe tumse pyaar hai baby")
    assert len(queries) == 2
    assert all("pyaar" not in q.casefold() and "tumse" not in q.casefold() for q in queries)
    assert "girlfriend" in queries[1].casefold()


def test_hinglish_is_primary_reply_language_even_for_english_messages():
    from aiko.dialogue import DialogueManager
    dialogue = DialogueManager()
    assert dialogue.effective_language(1, "hinglish") == "hinglish"
    dialogue.preferred_language[1] = "en"
    assert dialogue.effective_language(1, "hinglish") == "en"


def test_always_mode_keeps_persona_questions_and_controls_local():
    assert not WebResearcher.should_search("What is your name bubu", "always")
    assert not WebResearcher.should_search("Baby stop", "always")
    assert not WebResearcher.should_search("Baby yrrr hinglish bolo na", "always")
    assert not WebResearcher.should_search("please stop", "always")


def test_personal_status_and_day_updates_never_trigger_web_search():
    messages = (
        "Me bhi thik hu babby 😚",
        "main bhi achha hoon baby",
        "I'm fine too, sweetheart",
        "Mera din bhi acha tha",
        "aaj ka din badhiya tha jaanu",
        "my day was good",
    )
    for message in messages:
        assert WebResearcher.is_local_conversation_control(message), message
        assert not WebResearcher.should_search(message, "always"), message
        assert not WebResearcher.should_search(message, "auto"), message


def test_explicit_search_still_overrides_local_chat_exceptions():
    assert WebResearcher.should_search("/search What is your name bubu", "off")
    assert WebResearcher.should_search("/search Baby stop", "off")


def test_identity_question_is_available_to_local_rule_engine():
    import yaml
    from pathlib import Path
    from aiko.engine import ResponseEngine

    root = Path(__file__).resolve().parents[1]
    persona = yaml.safe_load((root / "config" / "persona.yaml").read_text(encoding="utf-8"))
    engine = ResponseEngine(persona, str(root / "config" / "rules.yaml"))
    result = engine.match("What is your name bubu", {"affection": 60, "mood": "playful"}, user_id=321, lang="hinglish")
    assert result is not None
    assert result.rule_id == "who_is_bhawna"


def test_stop_request_gets_a_direct_local_boundary_reply():
    from aiko.dialogue import DialogueManager

    dialogue = DialogueManager()
    reply = dialogue.respond(456, "Baby stop", lang="hinglish")
    assert reply is not None
    assert reply.intent == "stop_request"
    assert any(word in reply.text.casefold() for word in ("ruk", "stopping", "pause"))


def test_phonetic_bonus_kiss_followup_uses_context_in_always_mode(monkeypatch):
    calls = []

    class NoisyDDGS:
        def text(self, query, **kwargs):
            calls.append(query)
            return [{"title": "Dedo mujhe bhi viral video", "href": "https://example.com/video", "body": "Funny YouTube short."}]

    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=NoisyDDGS))
    monkeypatch.setattr(WebResearcher, "_search_html", lambda self, query, limit: [])
    context = {"recent_messages": [
        {"role": "user", "text": "Hello jii babyyy kissi dedo na ek"},
        {"role": "assistant", "text": "idhar aao baby 😚💋 ek soft forehead kiss aur ek cheek pe"},
    ], "preferences": {"reply_language": "hinglish"}, "recent_searches": []}
    web = WebResearcher()
    prompt = "Dedo na ek or 😉"
    assert WebResearcher.response_intent(prompt, context) == "kiss"
    assert WebResearcher.should_search(prompt, "always", context)
    response = web.answer(prompt, "hinglish", context=context, mode="always")
    assert response is not None
    assert any(token in response.casefold() for token in ("bonus", "extra", "kiss"))
    assert "example.com" not in response
    assert "useful results" not in response.casefold()


def test_comfort_request_has_a_comforting_reply_even_with_noisy_search_results(monkeypatch):
    class NoisyDDGS:
        def text(self, query, **kwargs):
            return [{"title": "Funny viral jokes", "href": "https://example.com/jokes", "body": "Comedy and jokes."}]

    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=NoisyDDGS))
    monkeypatch.setattr(WebResearcher, "_search_html", lambda self, query, limit: [])
    web = WebResearcher()
    context = {"recent_messages": [
        {"role": "user", "text": "😭😭"},
        {"role": "assistant", "text": "uff, idhar aao 🫂 kya hua jaan—batana hai ya bas thodi der comfort chahiye?"},
    ], "preferences": {"reply_language": "hinglish"}, "recent_searches": []}
    response = web.answer("Comfort dedo aap", "hinglish", context=context, mode="always")
    assert response is not None
    assert any(token in response.casefold() for token in ("hug", "comfort", "aaram", "saans"))
    assert "thoda aur context" not in response.casefold()
    assert "example.com" not in response


def test_freeserp_keyless_json_payload_is_normalized():
    web = WebResearcher()
    monkeypatch_payload = {
        "results": [
            {"title": "William Shakespeare", "url": "https://example.org/shakespeare", "snippet": "English playwright and poet.", "lang": "en"},
            {"title": "Duplicate", "url": "https://example.org/shakespeare", "snippet": "Duplicate row."},
        ]
    }
    results = web._normalize_json_results(monkeypatch_payload, 4)
    assert results == [{
        "title": "William Shakespeare",
        "url": "https://example.org/shakespeare",
        "body": "English playwright and poet.",
    }]


def test_freeserp_search_uses_documented_keyless_open_web_endpoint(monkeypatch):
    calls = []
    web = WebResearcher()
    def fake_fetch(url, timeout=8.0):
        calls.append(url)
        return {"results": [{"title": "Python", "url": "https://python.org", "snippet": "Python language"}]}
    monkeypatch.setattr(web, "_fetch_json", fake_fetch)
    results = web._search_freeserp("Python current version", 3)
    assert results[0]["title"] == "Python"
    assert calls and calls[0].startswith("https://freeserp.ai/api.php?")
    assert "index=web" in calls[0]
    assert "lang=en" in calls[0]
    assert "size=3" in calls[0]
    assert "api_key" not in calls[0].casefold()


def test_search_provider_order_prefers_freeserp_and_uses_fallbacks(monkeypatch):
    web = WebResearcher()
    calls = []
    def free(query, limit):
        calls.append("freeserp")
        raise OSError("403 forbidden")
    def searx(query, limit):
        calls.append("searxng")
        return []
    def ddgs(query, limit):
        calls.append("ddgs")
        return [{"title": "Python docs", "url": "https://python.org", "body": "Official docs"}]
    monkeypatch.setattr(web, "_search_freeserp", free)
    monkeypatch.setattr(web, "_search_searxng", searx)
    monkeypatch.setattr(web, "_search_ddgs", ddgs)
    result = web.search("What is Python?", max_results=2)
    assert result[0]["title"] == "Python docs"
    assert calls[:3] == ["freeserp", "searxng", "ddgs"]


def test_provider_403_is_not_shown_as_raw_error_for_factual_prompt(monkeypatch):
    web = WebResearcher()
    monkeypatch.setattr(web, "search", lambda *args, **kwargs: (_ for _ in ()).throw(WebSearchUnavailable("HTTP 403 Forbidden from provider")))
    answer = web.answer("What is a very obscure thing?", "hinglish")
    assert "useful results nahi mile" in answer.casefold()
    assert "403" not in answer
    assert "forbidden" not in answer.casefold()


def test_repeat_query_is_cached_and_does_not_hit_provider_again(monkeypatch):
    web = WebResearcher()
    calls = []
    def free(query, limit):
        calls.append(query)
        return [{"title": "Python docs", "url": "https://python.org", "body": "official"}]
    monkeypatch.setattr(web, "_search_freeserp", free)
    monkeypatch.setattr(web, "_search_searxng", lambda *args: [])
    monkeypatch.setattr(web, "_search_ddgs", lambda *args: [])
    first = web.search("What is Python?", max_results=2)
    count = len(calls)
    second = web.search("What is Python?", max_results=2)
    assert first == second
    assert len(calls) == count


def test_provider_status_is_configuration_only_and_html_scraping_is_off_by_default(monkeypatch):
    monkeypatch.delenv("AIKO_ENABLE_DDG_HTML_FALLBACK", raising=False)
    monkeypatch.setenv("AIKO_SEARXNG_URL", "")
    status = WebResearcher().provider_status()
    assert "FreeSerp keyless JSON (primary)" in status
    assert "ddgs fallback" in status
    assert "DuckDuckGo HTML" not in status
    assert "not a live health check" in status


def test_searxng_provider_uses_only_configured_json_instance(monkeypatch):
    monkeypatch.setenv("AIKO_SEARXNG_URL", "https://searx.example.org")
    web = WebResearcher()
    calls = []
    def fake_fetch(url, timeout=8.0):
        calls.append(url)
        return {"results": [{"title": "Test source", "url": "https://example.org", "content": "A snippet"}]}
    monkeypatch.setattr(web, "_fetch_json", fake_fetch)
    result = web._search_searxng("test query", 2)
    assert result[0]["body"] == "A snippet"
    assert calls[0].startswith("https://searx.example.org/search?")
    assert "format=json" in calls[0]
    assert "language=en" in calls[0]


def test_what_are_you_doing_hinglish_shorthand_is_never_sent_to_web():
    for prompt in ("Kya kr rhi h meri jaanu", "kya kr rhe h baby", "Kya kar rahi ho jaanu?"):
        assert WebResearcher.is_local_conversation_control(prompt), prompt
        assert not WebResearcher.should_search(prompt, "always"), prompt
        assert not WebResearcher.should_search(prompt, "auto"), prompt


def test_reciprocal_hinglish_chat_statement_never_triggers_web(monkeypatch):
    prompts = (
        "😉me bhi aapse bt kr ra hu babyyy",
        "me bhi aapse baat kar raha hu baby 😚",
        "I'm also talking to you baby",
    )
    for prompt in prompts:
        assert WebResearcher.is_local_conversation_control(prompt), prompt
        assert not WebResearcher.should_search(prompt, "always"), prompt
        assert not WebResearcher.should_search(prompt, "auto"), prompt


def test_live_provider_diagnostic_uses_fixed_public_query_and_reports_success(monkeypatch):
    calls = []
    monkeypatch.setattr(WebResearcher, "_search_freeserp", lambda self, query, limit: calls.append((query, limit)) or [
        {"title": "Shakespeare", "url": "https://example.com/shakespeare", "body": "A playwright."}
    ])
    message = WebResearcher().test_primary_provider()
    assert calls == [("Who was William Shakespeare?", 2)]
    assert "reachable" in message.lower()
    assert "1 usable result" in message.lower()


def test_live_provider_diagnostic_hides_raw_provider_error(monkeypatch):
    monkeypatch.setattr(WebResearcher, "_search_freeserp", lambda self, query, limit: (_ for _ in ()).throw(OSError("secret query and raw response")))
    message = WebResearcher().test_primary_provider()
    assert "could not connect" in message.lower()
    assert "secret query" not in message.lower()
    assert "raw response" not in message.lower()
