from __future__ import annotations
import re

SUPPORTED_LANGUAGES = ("en", "hi", "hinglish")
# Hinglish is Bhawna's primary/default language: ambiguous messages with no
# clear English or Devanagari signal are treated as Hinglish.
DEFAULT_LANGUAGE = "hinglish"


# Explicit language requests should beat ordinary keyword detection. This is a
# tiny grammar, not an AI classifier, and is intentionally conservative.
_LANGUAGE_ACTION_RE = re.compile(
    r"\b(?:baat|speak|talk|reply|respond|answer|bolo|bolna|karo|kro|karna|kijiye|likho|write|language)\b",
    re.IGNORECASE,
)
_LANGUAGE_AUTO_RE = re.compile(
    r"\b(?:auto(?:matic)?(?:ally)?|auto.?detect|detect\s+language|normal\s+language|language\s+auto)\b",
    re.IGNORECASE,
)

def parse_language_request(text: str) -> str | None:
    """Return an explicitly requested language, or ``'auto'`` to resume detection.

    Examples: ``'Hinglish me baat kro na'``, ``'speak in English'`` and
    ``'Hindi mein reply karo'``. Ordinary mentions such as ``'I like Hindi
    movies'`` do not count as a request.
    """
    if not text or not text.strip():
        return None
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    if _LANGUAGE_AUTO_RE.search(cleaned) and re.search(r"\b(?:language|bol|baat|reply|speak|talk|detect)\b", cleaned):
        return "auto"
    if not _LANGUAGE_ACTION_RE.search(cleaned):
        return None
    if re.search(r"\bhinglish\b", cleaned):
        return "hinglish"
    if re.search(r"\bhindi\b|\bhindee\b", cleaned):
        return "hi"
    if re.search(r"\benglish\b|\benglis\b", cleaned):
        return "en"
    return None

# Devanagari block (Hindi script). Any occurrence means the user wrote Hindi.
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
# Latin-script word tokens (for romanized Hinglish / English).
_WORD_RE = re.compile(r"[a-z]+")

# Romanized-Hindi words that are (essentially) never valid English words.
# A single hit is treated as a confident Hinglish signal.
HINDI_STRONG = {
    "kya", "kyu", "kyun", "kyunki", "kaise", "kaisa", "kaisi", "kahaan", "kahan",
    "kaun", "konsa", "kaunsa", "nahi", "nahin", "haan", "achha", "acha", "theek",
    "thik", "tum", "tumhe", "tumhara", "tumhari", "tumhare", "aap", "aapko",
    "aapka", "aapki", "mujhe", "mujhko", "mera", "meri", "mere", "yaar", "yaaron",
    "bhai", "batao", "batana", "karna", "karo", "karunga", "karungi", "chahiye",
    "chahta", "chahti", "chahte", "matlab", "bilkul", "bahut", "aaj", "kal",
    "subah", "shaam", "raat", "khana", "khao", "paani", "ghar", "padhai", "dost",
    "pyaar", "pyar", "mohabbat", "zindagi", "udaas", "khush", "mazaa", "maza",
    "ladka", "ladki", "ladke", "baccha", "bachche", "bacchi", "jaldi", "kidhar",
    "idhar", "udhar", "yahan", "yaha", "wahan", "waha", "namaste", "shukriya",
    "dhanyavaad", "arre", "arey", "wapas", "isliye", "wajah", "faisla", "sochna",
    "socho", "samajhna", "samajh", "lagta", "lagti", "dekho", "dekha", "suno",
    "bolo", "chalo", "ruko", "baitho", "utho", "soja", "sojao", "neend", "bhook",
    "bhookh", "pyas", "mushkil", "asaan", "kharab", "badhiya", "zabardast",
    "kadak", "tere", "tera", "teri", "unka", "unki", "uska", "uski", "inka",
    "inki", "humara", "humko", "humein", "hamara", "waise", "aise", "sach",
    "jhooth", "aansoo", "hansi", "khushi", "tanhai", "akela", "akeli", "dhadkan",
    "yaari", "karni", "karne", "karoge", "karte", "karta", "karti", "karke",
    "aayega", "aayegi", "jayega", "jayegi", "milega", "milegi", "dekhna", "sunna",
    "kehna", "kehta", "kehti", "bataye", "rehna", "raho", "aana", "aaja", "aao",
    "jao", "ruk", "bata", "uth", "chalte", "milo", "dekhoge", "bataiye", "suniye",
    "dekhiye", "thaka", "thaki", "thakan", "sukoon", "safar", "manzil", "raaste",
    "nakhre", "nakhra", "sharmana", "sharma", "ghussa", "gussa", "dosti",
    "yaadein", "bechain", "betab", "khamosh", "sunao", "bataun", "karega",
    "karegi", "karenge", "likhna", "padhna", "jaana", "uthna", "sona", "khilona",
    "jahan", "kabhi", "hamesha",
}

# Romanized-Hindi words that also occur in English or are too short/common on
# their own. They only count as a signal when corroborated.
HINDI_WEAK = {
    "hai", "hain", "ho", "hu", "hun", "hoon", "tha", "thi", "se", "ko",
    "ki", "ke", "ka", "mein", "par", "aur", "bhi", "na", "mat", "ab", "phir",
    "tab", "jab", "tak", "agar", "lekin", "magar", "kuch", "kisi", "koi", "yeh",
    "ye", "wo", "woh", "jo", "tu", "sab", "bas", "dil", "baat", "baatein",
    "zyada", "sirf", "abhi", "parso", "log", "lage", "liye", "wala", "wali",
    "raha", "rahe", "rahi", "gaya", "gayi", "gaye", "thoda", "pata", "kaam",
    "din", "waqt", "gum", "saath", "bina", "chal", "hoti", "hota", "hoga",
    "hogi", "aata", "aati", "jaata", "jaati", "mila", "mili", "mil", "dekh",
    "sun", "bol", "bola", "kaho", "kaha", "chalna", "chalta", "chalti", "dono",
    "laga", "lagi", "kar", "diya", "diye", "liya",
}

# Common English function/content words used to confirm an English message.
ENGLISH_MARKERS = {
    "the", "is", "are", "am", "was", "were", "be", "been", "being", "do", "does",
    "did", "doing", "have", "has", "had", "a", "an", "and", "or", "but", "if",
    "then", "else", "when", "while", "of", "at", "by", "for", "with", "about",
    "into", "through", "before", "after", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "once", "here", "there", "all", "any",
    "both", "each", "more", "most", "other", "some", "such", "no", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just", "should",
    "now", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "this", "that", "these",
    "those", "what", "which", "who", "how", "why", "where", "because", "as",
    "until", "really", "please", "thanks", "thank", "hello", "hey", "hi", "yes",
    "ok", "okay", "good", "bad", "morning", "night", "evening", "love", "like",
    "want", "need", "feel", "think", "know", "tell", "say", "said", "make",
    "made", "get", "got", "go", "going", "come", "see", "look", "help", "today",
    "tomorrow", "yesterday", "work", "time", "day", "people", "thing", "things",
    "way", "much", "many", "well", "right", "sorry", "bye", "goodbye",
}

def detect_language(text: str) -> tuple[str, bool]:
    """Detect the language of a message.

    Returns a tuple ``(language, confident)`` where ``language`` is one of
    ``"en"``, ``"hi"`` (Devanagari Hindi) or ``"hinglish"`` (romanized Hindi).
    ``confident`` is ``False`` when the message carries no clear signal, letting
    callers fall back to a sticky per-user preference instead of guessing.
    """
    if not text or not text.strip():
        return (DEFAULT_LANGUAGE, False)
    requested = parse_language_request(text)
    if requested in SUPPORTED_LANGUAGES:
        return (requested, True)
    if _DEVANAGARI_RE.search(text):
        return ("hi", True)
    words = _WORD_RE.findall(text.lower())
    if not words:
        return (DEFAULT_LANGUAGE, False)
    strong = sum(1 for w in words if w in HINDI_STRONG)
    weak = sum(1 for w in words if w in HINDI_WEAK)
    eng = sum(1 for w in words if w in ENGLISH_MARKERS)

    # A single unambiguous romanized-Hindi word wins outright.
    if strong >= 1:
        return ("hinglish", True)
    # Multiple weak Hindi words, not outnumbered by English markers.
    if weak >= 2 and weak > eng:
        return ("hinglish", True)
    # A single weak Hindi word with no English signal at all.
    if weak == 1 and eng == 0:
        return ("hinglish", True)
    # Clear English signal.
    if eng >= 2:
        return ("en", True)
    if eng >= 1 and len(words) >= 5:
        return ("en", True)
    # Ambiguous: no reliable signal. Let the caller keep the sticky language.
    return (DEFAULT_LANGUAGE, False)

class LanguageTracker:
    """Per-user sticky language preference.

    Confident detections update the stored language; ambiguous messages inherit
    whatever language the user last established (or the default on first sight).
    """

    def __init__(self) -> None:
        self._lang: dict[int, str] = {}

    def seed(self, user_id: int, lang: str | None) -> None:
        """Load a persisted language once (e.g. after a restart)."""
        if lang in SUPPORTED_LANGUAGES and user_id not in self._lang:
            self._lang[user_id] = lang

    def observe(self, user_id: int, text: str) -> str:
        """Update the sticky language from a message and return the effective one."""
        detected, confident = detect_language(text)
        if confident:
            self._lang[user_id] = detected
        return self._lang.get(user_id, detected)

    def get(self, user_id: int, default: str = DEFAULT_LANGUAGE) -> str:
        return self._lang.get(user_id, default)

    def set(self, user_id: int, lang: str) -> None:
        if lang in SUPPORTED_LANGUAGES:
            self._lang[user_id] = lang

    def forget(self, user_id: int) -> None:
        self._lang.pop(user_id, None)
