from aiko.text_style import apply_texting_style, detect_texting_style, normalize_for_matching
from aiko.dialogue import DialogueManager
from aiko.web_research import WebResearcher
from aiko.local_brain import LocalBrain
from aiko.conversation_learning import LocalConversationLearning
from aiko.engine import ResponseEngine


def test_normalizer_handles_elongated_letters_and_short_forms():
    assert normalize_for_matching("Babyyyy u r sooo cuteee plssss") == "Baby you are so cute please"
    assert normalize_for_matching("hru babyyyy") == "how are you baby"
    assert normalize_for_matching("i luv uuuu") == "i love you"
    assert normalize_for_matching("krdo plzz") == "kar do please"
    assert normalize_for_matching("Me bhi thik hu babby 😚") == "main bhi thik hoon baby 😚"


def test_normalizer_handles_emojified_hinglish_chat_statement():
    assert normalize_for_matching("😉me bhi aapse bt kr ra hu babyyy") == "main bhi aapse baat kar raha hoon baby"


def test_dialogue_matches_stretched_hinglish_and_short_forms():
    dialogue = DialogueManager()
    cases = {
        "hiiiiii babyyyy 😚": "greeting",
        "Keseee hooo babyyyy 😚😚💋": "wellbeing",
        "I luv uuuu baby 💋": "love",
        "u r cuteee": "compliment",
        "u r sooo cuteee": "compliment",
        "gimme a kiss plssss": "kiss",
    }
    for message, intent in cases.items():
        reply = dialogue.respond(551, message, "hinglish")
        assert reply is not None, message
        assert reply.intent == intent, (message, reply.intent, intent)
        assert reply.text.strip()


def test_reciprocal_hinglish_statement_gets_natural_local_reply():
    dialogue = DialogueManager()
    first = "Kya kr rhi h meri jaanu"
    first_reply = dialogue.respond(771, first, "hinglish")
    assert first_reply is not None and first_reply.intent == "what_doing"
    dialogue.note_response(771, first_reply.text, first_reply.intent)

    reply = dialogue.respond(771, "😉me bhi aapse bt kr ra hu babyyy", "hinglish")
    assert reply is not None
    assert reply.intent == "reciprocal_chat"
    assert "context do" not in reply.text.casefold()
    assert any(token in reply.text.casefold() for token in ("company", "baat", "gossip", "pasand"))


def test_yaml_engine_rules_also_match_shortened_text():
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    persona = {"name": "Bhawna", "speech_style": {"lowercase": True, "max_message_length": 180}}
    engine = ResponseEngine(persona, str(root / "config" / "rules.yaml"))
    result = engine.match("I luv uuuu baby 💋", user_state={"affection": 60})
    assert result is not None
    assert result.rule_id == "love_miss"


def test_stretched_checkins_do_not_trigger_web_even_in_always_mode():
    for message in ("Keseee hooo babyyyy 😚", "hru babyyyy", "heyyyy jaanuuu"):
        assert WebResearcher.is_local_conversation_control(message), message
        assert not WebResearcher.should_search(message, "always"), message


def test_learned_phrases_match_variations_of_user_typing(tmp_path):
    brain = LocalBrain(tmp_path / "brain.json")
    assert brain.learn("how are you baby", "mast hoon ji 💗", 9)
    assert brain.match("hru babyyyy", 9) == "mast hoon ji 💗"


def test_texting_style_is_learned_persistently_and_mirrored(tmp_path):
    learning = LocalConversationLearning(tmp_path / "learning.json")
    learning.observe(2, "user", "babyyyy ily plssss 😭💋")
    preferences = learning.context_for(2)["preferences"]
    assert preferences["elongated_spelling"] == "on"
    assert preferences["short_forms"] == "on"
    # Preferences survive a process restart because the learner stores them in JSON.
    restarted = LocalConversationLearning(tmp_path / "learning.json")
    assert restarted.context_for(2)["preferences"]["elongated_spelling"] == "on"
    assert restarted.context_for(2)["preferences"]["short_forms"] == "on"
    assert apply_texting_style("love you too, baby 💗", preferences) == "love u too, babyyyy 💗"


def test_non_stylized_users_do_not_get_unrequested_stretching():
    assert detect_texting_style("How are you today?") == {
        "elongated_spelling": False,
        "short_forms": False,
    }
    assert apply_texting_style("love you too, baby 💗", {}) == "love you too, baby 💗"


def test_informal_hinglish_what_doing_messages_match_and_stay_local():
    messages = (
        "Kya kr rhi h meri jaanu",
        "kya kr rhe h baby",
        "Kya kar rahi ho jaanu?",
        "kya kr rhi h",
    )
    for message in messages:
        reply = DialogueManager().respond(771, message, "hinglish")
        assert reply is not None, message
        assert reply.intent == "what_doing", (message, reply.intent)
        assert "context do" not in reply.text.casefold(), reply.text
        assert WebResearcher.is_local_conversation_control(message), message
        assert not WebResearcher.should_search(message, "always"), message
        assert not WebResearcher.should_search(message, "auto"), message
