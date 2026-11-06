from aiko.dialogue import DialogueManager


def test_sample_conversation_gets_relevant_replies():
    d = DialogueManager()
    samples = {
        "Hello ji": "greeting",
        "Ache hai ji hum to aap btao kese ho": "wellbeing",
        "Kha chodu 🌚": "innuendo",
        "😂umwaahhh babby": "laugh",
        "Baby kissi dedo n": "kiss",
        "Kiss dedo": "kiss",
        "Kya huaa": "direct_question",
        "dark joke suna": "dark_humor",
    }
    for message, intent in samples.items():
        reply = d.respond(42, message, "hinglish")
        assert reply is not None, message
        assert reply.intent == intent, message
        assert reply.text.strip(), message


def test_short_affection_answer_is_not_generic_fallback():
    d = DialogueManager()
    d.note_intent(42, "what_matters")
    reply = d.respond(42, "Aap", "hinglish")
    assert reply is not None
    assert reply.intent == "affectionate_reaction"
    assert "blush" in reply.text or "pyaar" in reply.text or "sharma" in reply.text


def test_repeat_response_is_varied_when_possible():
    d = DialogueManager()
    seen = {d.respond(42, "kiss dedo", "hinglish").text for _ in range(8)}
    assert len(seen) > 1


def test_affectionate_hinglish_wellbeing_variants_get_direct_wellbeing_replies():
    d = DialogueManager()
    for message in ("Kese ho babyy 😚😚💋", "Aap kese ho me to acha hu 💋😋", "Kese ho baby?"):
        reply = d.respond(88, message, "hinglish")
        assert reply is not None, message
        assert reply.intent == "wellbeing", (message, reply.intent)
        assert "context do" not in reply.text.lower(), reply.text
