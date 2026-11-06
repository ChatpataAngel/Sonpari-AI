import json
import re
from pathlib import Path

from aiko.conversation_hub import OfflineConversationHub
from aiko.dialogue import DialogueManager


LIBRARY_PATH = Path(__file__).parents[1] / "aiko" / "conversation_library.json"


def test_v26_library_has_broad_original_multilingual_coverage():
    payload = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    entries = payload["entries"]
    assert payload["schema_version"] >= 2
    assert len(entries) >= 90
    assert len({entry["intent"] for entry in entries}) == len(entries)
    response_count = sum(
        len(pool)
        for entry in entries
        for pool in entry["responses"].values()
    )
    assert response_count >= 560
    for entry in entries:
        assert set(entry["responses"]) >= {"hinglish", "hi", "en"}
        assert all(entry["responses"][language] for language in ("hinglish", "hi", "en"))


def test_v26_library_patterns_are_valid_regexes():
    payload = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    for entry in payload["entries"]:
        for pattern in entry["patterns"]:
            re.compile(pattern, re.I)


def test_specific_topics_route_before_broad_keyword_rules():
    cases = {
        "I am really worried that my interview is coming up soon and I might blank": "job_interview",
        "I feel very awkward about what I said at lunch yesterday": "awkward_moment",
        "I love rain and sitting by window": "rainy_mood",
        "I love pizza so much": "food_preference",
        "I love cricket": "sports_chat",
        "I am nervous about my exam": "exam_anxiety",
        "Can you explain recursion to me like I am a beginner": "explanation_request",
        "We need to plan a vacation this summer": "trip_plans",
        "My best friend has been ignoring me": "friend_conflict",
        "I have a coding issue with Python loops": "coding_help",
    }
    for message, expected_intent in cases.items():
        reply = DialogueManager().respond(5150, message, "hinglish")
        assert reply is not None, message
        assert reply.intent == expected_intent, (message, reply.intent, expected_intent)
        assert reply.text.strip()


def test_explicit_direct_chat_flirting_and_boundaries_keep_priority():
    cases = {
        "Kya kr rhi h meri jaanu": "what_doing",
        "I love you": "love",
        "😋I wanna eat you out": "sexual_flirt",
        "Comfort dedo aap": "comfort_request",
        "Baby stop": "stop_request",
    }
    for message, expected_intent in cases.items():
        reply = DialogueManager().respond(5151, message, "hinglish")
        assert reply is not None, message
        assert reply.intent == expected_intent, (message, reply.intent, expected_intent)


def test_specific_food_preference_works_in_all_supported_reply_languages():
    hub = OfflineConversationHub()
    for language in ("hinglish", "hi", "en"):
        reply = hub.respond("I love pizza so much", language, only_intents={"food_preference"})
        assert reply is not None and reply[0] == "food_preference"
        assert reply[1].strip()


def test_no_response_library_route_hijacks_commands():
    hub = OfflineConversationHub()
    for command in ("/help", "/search I love cricket", "/web off", "/forgetall"):
        assert hub.respond(command, "hinglish") is None


def test_each_new_topic_has_a_working_representative_example():
    payload = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    new_entries = payload["entries"][23:]
    for index, entry in enumerate(new_entries):
        examples = entry.get("examples", [])
        assert examples, entry["intent"]
        reply = DialogueManager().respond(9000 + index, examples[0], "hinglish")
        assert reply is not None, (entry["intent"], examples[0])
        # Explicit, established compliment handling intentionally outranks the
        # more generic supplemental compliment-acceptance intent.
        if entry["intent"] == "compliment_acceptance":
            assert reply.intent == "compliment"
        else:
            assert reply.intent == entry["intent"], (
                entry["intent"], examples[0], reply.intent
            )
