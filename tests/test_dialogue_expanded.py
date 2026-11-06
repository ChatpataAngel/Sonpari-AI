import random

from aiko.dialogue import DialogueManager
from aiko.dialogue_rules import RULES
from aiko.language import detect_language, parse_language_request


def test_language_request_is_a_command_not_smalltalk():
    dm = DialogueManager(random.Random(1))
    reply = dm.respond(7, "Hinglish me baat kro na", "en")
    assert reply is not None
    assert reply.intent == "language_preference"
    assert "hinglish" in reply.text.lower()
    assert dm.effective_language(7, "en") == "hinglish"


def test_language_preference_beats_later_english_detection():
    dm = DialogueManager(random.Random(4))
    dm.respond(7, "Hinglish me baat kro na", "en")
    # Caller may detect this message as English, but explicit preference wins.
    reply = dm.respond(7, "hello", "en")
    assert reply is not None and reply.intent == "greeting"
    assert any(token in reply.text.lower() for token in ("tum", "jaan", "ji", "aa", "kya"))


def test_language_parser_handles_hinglish_hindi_and_english():
    assert parse_language_request("Hinglish me baat kro na") == "hinglish"
    assert parse_language_request("Hindi mein reply karo") == "hi"
    assert parse_language_request("please speak in English") == "en"
    assert parse_language_request("I like Hindi movies") is None
    assert detect_language("Hinglish me baat kro na") == ("hinglish", True)


def test_clarification_repairs_a_vague_previous_question():
    dm = DialogueManager(random.Random(0))
    dm.note_response(10, "tum is baare mein kya sochte ho?", "fallback")
    reply = dm.respond(10, "Kis baare me?", "hinglish")
    assert reply is not None and reply.intent == "clarification"
    assert "mera matlab tha" in reply.text.lower()
    assert "kya hua" in reply.text.lower() or "mood" in reply.text.lower()


def test_arey_gets_an_actual_reaction_not_a_random_question():
    dm = DialogueManager(random.Random(0))
    reply = dm.respond(9, "Areey", "hinglish")
    assert reply is not None and reply.intent == "filler_reaction"
    assert "arey" in reply.text.lower() or "cliffhanger" in reply.text.lower()


def test_sample_conversation_does_not_drop_into_generic_fallback():
    dm = DialogueManager(random.Random(3))
    samples = [
        ("hello", "greeting"),
        ("Hello ji", "greeting"),
        ("Hinglish me baat kro na", "language_preference"),
        ("Kis baare me?", "clarification"),
        ("Areey", "filler_reaction"),
        ("Kha chodu 🌚", "innuendo"),
        ("😂umwaahhh babby", "laugh"),
        ("Baby kissi dedo n", "kiss"),
        ("Kiss dedo", "kiss"),
        ("dark joke suna", "dark_humor"),
        ("I'm bored", "bored"),
        ("tell me a joke", "joke"),
    ]
    for message, expected in samples:
        reply = dm.respond(42, message, "hinglish")
        assert reply is not None, message
        assert reply.intent == expected, (message, reply.intent, expected)
        assert reply.text.strip(), message



def test_playful_hinglish_body_compliment_gets_character_reply_locally():
    dm = DialogueManager(random.Random(6))
    reply = dm.respond(111, "baby aapke vo bade bade dudu 😹🧿💝", "hinglish")
    assert reply is not None
    assert reply.intent == "playful_body_compliment"
    assert any(token in reply.text.casefold() for token in ("compliment", "tareef", "blush", "teasing"))
    assert "can't help" not in reply.text.casefold()


def test_rule_packs_are_unique_and_have_all_three_languages():
    intents = [intent for intent, _pattern, _pools in RULES]
    assert len(intents) >= 50
    assert len(intents) == len(set(intents))
    for intent, pattern, pools in RULES:
        assert pattern.search("") is None or intent == "clarification"
        assert set(pools) == {"hinglish", "hi", "en"}
        assert all(pools[lang] for lang in pools), intent


def test_context_is_updated_after_bot_turn():
    dm = DialogueManager(random.Random(2))
    first = dm.respond(4, "hello ji", "hinglish")
    dm.note_response(4, first.text, first.intent)
    second = dm.respond(4, "Kis baare me?", "hinglish")
    assert second and second.intent == "clarification"


def test_ambiguous_greeting_defaults_to_hinglish():
    from aiko.language import LanguageTracker
    tracker = LanguageTracker()
    assert tracker.observe(88, "hello") == "hinglish"
    assert tracker.observe(88, "Hello ji") == "hinglish"


def test_good_status_answer_does_not_match_the_word_hi_as_a_greeting():
    dm = DialogueManager(random.Random(1))
    reply = dm.respond(71, "Acha hi hu ji", "hinglish")
    assert reply is not None
    assert reply.intent == "status_good"
    assert "good" in reply.text.lower() or "achha" in reply.text.lower() or "badhiya" in reply.text.lower()


def test_one_word_kha_gets_a_local_clarification_not_a_topic_fallback():
    dm = DialogueManager(random.Random(1))
    reply = dm.respond(72, "Kha", "hinglish")
    assert reply is not None and reply.intent == "short_unclear"
    assert "typo" in reply.text.lower() or "aadha" in reply.text.lower() or "message" in reply.text.lower()


def test_yes_after_a_kiss_remains_in_the_romantic_context():
    dm = DialogueManager(random.Random(1))
    dm.note_response(73, "happy now, or do i need a written application?", "dialogue:kiss")
    reply = dm.respond(73, "Yes", "hinglish")
    assert reply is not None and reply.intent == "affirmative_followup"
    assert "kiss" in reply.text.lower() or "application" in reply.text.lower()


def test_sexual_innuendo_is_acknowledged_without_generic_confusion():
    dm = DialogueManager(random.Random(1))
    for message in ("😋I wanna eat you out", "I wanna eat your pussy"):
        reply = dm.respond(74, message, "hinglish")
        assert reply is not None and reply.intent == "sexual_flirt"
        assert any(token in reply.text.lower() for token in ("spicy", "explicit", "flirt", "graphic", "teasing"))


def test_adult_mode_questions_get_an_explicit_answer():
    dm = DialogueManager(random.Random(1))
    for message in ("Are you sexual ?", "18+ or not"):
        reply = dm.respond(75, message, "en")
        assert reply is not None and reply.intent == "adult_mode_question"
        assert "fictional" in reply.text.lower() or "flirty" in reply.text.lower() or "graphic" in reply.text.lower()


def test_flirty_emojis_and_crying_emojis_are_not_mistaken_for_laughter():
    dm = DialogueManager(random.Random(1))
    flirt = dm.respond(76, "🌚😚", "hinglish")
    cry = dm.respond(77, "😭😭", "hinglish")
    assert flirt is not None and flirt.intent == "flirty_emoji"
    assert cry is not None and cry.intent == "cry_reaction"


def test_explicit_hinglish_preference_beats_english_phrases():
    dm = DialogueManager(random.Random(1))
    dm.respond(78, "Hinglish me baat kro na", "en")
    reply = dm.respond(78, "I love you", "en")
    assert reply is not None and reply.intent == "love"
    assert any(token in reply.text.lower() for token in ("jaan", "pyaar", "tum", "sharma", "baby"))


def test_hmm_is_a_thinking_signal_not_another_cliffhanger_prompt():
    dm = DialogueManager(random.Random(1))
    reply = dm.respond(79, "Hmm", "hinglish")
    assert reply is not None and reply.intent == "thinking_reaction"
    assert "topic" in reply.text.lower() or "soch" in reply.text.lower() or "aaram" in reply.text.lower()


def test_kiss_followup_understands_phonetic_hinglish_or_spelling():
    dm = DialogueManager(random.Random(3))
    first = dm.respond(987, "Hello jii babyyy kissi dedo na ek", "hinglish")
    assert first is not None and first.intent == "kiss"
    dm.note_response(987, first.text, "dialogue:kiss")
    followup = dm.respond(987, "Dedo na ek or 😉", "hinglish")
    assert followup is not None and followup.intent == "kiss_followup"
    assert any(token in followup.text.casefold() for token in ("bonus", "extra", "kiss"))


def test_direct_comfort_request_gives_comfort_without_asking_for_context():
    dm = DialogueManager(random.Random(4))
    reply = dm.respond(988, "Comfort dedo aap", "hinglish")
    assert reply is not None and reply.intent == "comfort_request"
    assert any(token in reply.text.casefold() for token in ("hug", "comfort", "saans"))
    assert "mujhe thoda aur context" not in reply.text.casefold()


def test_checkin_reply_and_good_day_update_are_not_generic_fallbacks():
    from aiko.web_research import WebResearcher

    dm = DialogueManager(random.Random(19))
    first = dm.respond(989, "Kese ho aap ?", "hinglish")
    assert first is not None and first.intent == "wellbeing"
    dm.note_response(989, first.text, first.intent)

    status = dm.respond(989, "Me bhi thik hu babby 😚", "hinglish")
    assert status is not None and status.intent == "status_good"
    assert "context do" not in status.text.casefold()
    assert not WebResearcher.should_search("Me bhi thik hu babby 😚", "always")
    assert not WebResearcher.should_search("Me bhi thik hu babby 😚", "auto")

    dm.note_response(989, "tumhara din kaisa gaya?", "wellbeing")
    day = dm.respond(989, "Mera din bhi acha tha", "hinglish")
    assert day is not None and day.intent == "day_update_good"
    assert "context do" not in day.text.casefold()
    assert not WebResearcher.should_search("Mera din bhi acha tha", "always")
    assert not WebResearcher.should_search("Mera din bhi acha tha", "auto")
