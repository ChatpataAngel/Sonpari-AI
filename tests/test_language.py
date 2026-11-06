import pytest
from aiko.language import detect_language, LanguageTracker, DEFAULT_LANGUAGE

# (message, expected_language, expected_confident)
CASES = [
    ("hello how are you", "en", True),
    ("i am sad today", "en", True),
    ("good morning", "en", True),
    ("what are you doing", "en", True),
    ("love you", "en", True),
    ("kya haal hai", "hinglish", True),
    ("kaise ho bhai", "hinglish", True),
    ("mujhe neend aa rahi hai", "hinglish", True),
    ("aaj bahut khush hoon", "hinglish", True),
    ("tum kahan ho", "hinglish", True),
    ("mai thak gaya hoon", "hinglish", True),
    ("ok theek hai", "hinglish", True),
    ("मैं ठीक हूँ", "hi", True),
    ("आज बहुत खुश हूँ", "hi", True),
    # Hinglish is the primary/default: ambiguous messages fall back to it.
    ("", "hinglish", False),
    ("ok", "hinglish", False),
    ("hmm", "hinglish", False),
    ("😂", "hinglish", False),
    ("...", "hinglish", False),
]


@pytest.mark.parametrize("text,lang,confident", CASES)
def test_detect_language(text, lang, confident):
    got_lang, got_confident = detect_language(text)
    assert got_lang == lang
    assert got_confident is confident


def test_tracker_sticky_on_ambiguous():
    t = LanguageTracker()
    assert t.observe(1, "kya haal hai") == "hinglish"
    # Ambiguous follow-up keeps the previous language.
    assert t.observe(1, "ok") == "hinglish"
    assert t.observe(1, "😂") == "hinglish"


def test_tracker_switches_language():
    t = LanguageTracker()
    assert t.observe(2, "hello there") == "en"
    assert t.observe(2, "kya kar rahe ho") == "hinglish"
    assert t.observe(2, "i'm fine now") == "en"


def test_tracker_default_when_ambiguous_first():
    t = LanguageTracker()
    # Hinglish is the primary default language.
    assert t.observe(3, "ok") == "hinglish"


def test_tracker_seed_and_set():
    t = LanguageTracker()
    t.seed(4, "hi")
    assert t.get(4) == "hi"
    # Seed does not overwrite an already-seen user.
    t.seed(4, "en")
    assert t.get(4) == "hi"
    t.set(4, "hinglish")
    assert t.get(4) == "hinglish"
    # Invalid languages are ignored.
    t.set(4, "xx")
    assert t.get(4) == "hinglish"
