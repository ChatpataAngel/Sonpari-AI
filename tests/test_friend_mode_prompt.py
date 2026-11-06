from aiko.multi_ai import MultiAIClient


def test_friend_prompt_stays_platonic():
    client = MultiAIClient(persona={"name": "Bhawna", "age": 21})
    prompt = client._build_system_prompt("en", relationship_role="friend").lower()
    assert "your friend, not your romantic partner" in prompt
    assert "no romantic roleplay" in prompt
    assert "kindly keep the boundary" in prompt


def test_bf_prompt_allows_affectionate_companion_style():
    client = MultiAIClient(persona={"name": "Bhawna", "age": 21})
    prompt = client._build_system_prompt("en", relationship_role="bf").lower()
    assert "verified bf-tier access" in prompt
    assert "affectionate romantic-partner style" in prompt


def test_friend_local_reply_does_not_mirror_romance():
    from aiko.relationship import local_friend_reply
    assert "friend mode" in local_friend_reply("I love you", "en").lower()
    assert "platonic" in local_friend_reply("kiss me", "en").lower()


def test_friend_local_reply_handles_basic_messages():
    from aiko.relationship import local_friend_reply
    assert "how's it going" in local_friend_reply("hello", "en").lower()
    assert "you're welcome" in local_friend_reply("thank you", "en").lower()


def test_friend_proactive_greetings_are_platonic():
    from aiko.relationship import local_friend_greeting
    for lang in ("hinglish", "hi", "en"):
        for kind in ("checkin", "morning", "night"):
            reply = local_friend_greeting(kind, lang).lower()
            assert "baby" not in reply
            assert "love you" not in reply
