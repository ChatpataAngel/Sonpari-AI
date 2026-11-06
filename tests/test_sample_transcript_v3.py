"""Regression coverage for the user's latest Hinglish companion transcript."""
from aiko.dialogue import DialogueManager


def test_latest_transcript_uses_specific_contextual_intents():
    dialogue = DialogueManager()
    user_id = 9001
    transcript = [
        ("Hinglish me baat kro na", "language_preference"),
        ("Hello", "greeting"),
        ("Acha hi hu ji", "status_good"),
        ("Kha", "short_unclear"),
        ("Hmm", "thinking_reaction"),
        ("I love you", "love"),
        ("Acha ji", "acknowledgement"),
        ("Kissi dedo", "kiss"),
        ("Yes", "affirmative_followup"),
        ("😋I wanna eat you out", "sexual_flirt"),
        ("🌚😚", "flirty_emoji"),
        ("I wanna eat your pussy", "sexual_flirt"),
        ("😭😭", "cry_reaction"),
        ("Are you sexual ?", "adult_mode_question"),
        ("18+ or not", "adult_mode_question"),
    ]
    for message, expected_intent in transcript:
        reply = dialogue.respond(user_id, message, lang="en")
        assert reply is not None, f"No direct reply for {message!r}"
        assert reply.intent == expected_intent, (message, reply.intent, expected_intent)
        assert reply.text.strip()
        dialogue.note_response(user_id, reply.text, reply.intent)

    # The explicit preference should survive otherwise-English message text.
    assert dialogue.effective_language(user_id, "en") == "hinglish"
