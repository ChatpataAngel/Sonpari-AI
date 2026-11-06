import json
from pathlib import Path

from aiko.conversation_hub import OfflineConversationHub
from aiko.dialogue import DialogueManager


def test_library_has_multilingual_entries_and_original_authored_data():
    path = Path(__file__).parents[1] / "aiko" / "conversation_library.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] >= 2
    assert len(payload["entries"]) >= 90
    for entry in payload["entries"]:
        assert set(entry["responses"]) >= {"hinglish", "hi", "en"}
        assert all(entry["responses"][lang] for lang in ("hinglish", "hi", "en"))


def test_offline_library_routes_everyday_conversation_gaps():
    hub = OfflineConversationHub()
    cases = {
        "I feel sad": "feeling_low",
        "I am overwhelmed": "overwhelmed",
        "I have no one": "loneliness",
        "I need motivation": "motivation_request",
        "Can I vent?": "venting",
        "I don't want advice": "no_advice",
        "Ask me a question": "ask_me_question",
        "Change the topic": "change_topic",
        "keep me company": "want_company",
        "I passed": "success_share",
    }
    for message, expected_intent in cases.items():
        result = hub.respond(message, "hinglish")
        assert result is not None, message
        assert result[0] == expected_intent, (message, result)
        assert result[1].strip(), message


def test_dynamic_decision_help_personalizes_both_options():
    result = OfflineConversationHub().respond("I can't decide between tea and coffee", "en")
    assert result is not None
    assert result[0] == "decision_help"
    assert "tea" in result[1]
    assert "coffee" in result[1]


def test_library_respects_hindi_and_english_pools():
    hindi = OfflineConversationHub().respond("I need motivation", "hi")
    english = OfflineConversationHub().respond("I need motivation", "en")
    assert hindi and any(ch in hindi[1] for ch in "हैजी")
    assert english and "you" in english[1].lower()


def test_local_library_never_takes_over_commands():
    hub = OfflineConversationHub()
    for command in ("/help", "/search I feel sad", "/forgetall"):
        assert hub.respond(command, "hinglish") is None


def test_dialogue_manager_integrates_library_after_existing_direct_rules():
    d = DialogueManager()
    tired = d.respond(900, "I am tired", "hinglish")
    success = d.respond(901, "I passed", "hinglish")
    assert tired and tired.intent in {"feeling_tired", "tired", "fatigue"}
    assert success and success.intent in {"success", "success_share"}


def test_library_keeps_existing_romance_intent_priority():
    d = DialogueManager()
    reply = d.respond(902, "I love you", "hinglish")
    assert reply is not None
    assert reply.intent == "love"
    assert reply.intent != "interest_share"


def test_missing_library_does_not_crash_hub(monkeypatch):
    hub = OfflineConversationHub()
    monkeypatch.setattr(hub, "_library_entries", [])
    assert hub.respond("I am overwhelmed", "hinglish") is None
