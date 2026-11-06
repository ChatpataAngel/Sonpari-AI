"""Lightweight texting-style support for Aiko; no AI model or network required.

normalize_for_matching() is only for intent/phrase matching. Callers should keep
and store the original user message so the user's voice and punctuation remain
available for local conversation memory.
"""
from __future__ import annotations

import re
from typing import Any

# Common chat abbreviations expanded only for intent matching. This is
# deliberately conservative: it should improve matching without rewriting the
# original message shown to the user or saved in conversation history.
_TOKEN_REPLACEMENTS = {
    "bby": "baby",
    # Common double-letter affectionate spelling (distinct from elongated
    # "babyyyy", which is already collapsed by the repeated-letter pass).
    "babby": "baby",
    "babyy": "baby",
    "bbz": "babes",
    "pls": "please",
    "plz": "please",
    "thx": "thanks",
    "ty": "thanks",
    "ily": "i love you",
    "ilysm": "i love you so much",
    "ilyt": "i love you too",
    "idk": "i don't know",
    "idc": "i don't care",
    "tbh": "to be honest",
    "ngl": "not gonna lie",
    "btw": "by the way",
    "rn": "right now",
    "wbu": "what about you",
    "hru": "how are you",
    "wru": "where are you",
    "wyd": "what are you doing",
    "wya": "where are you",
    "wdym": "what do you mean",
    "wym": "what do you mean",
    "ikr": "i know right",
    "imo": "in my opinion",
    "imho": "in my humble opinion",
    "fyi": "for your information",
    "tysm": "thanks so much",
    "gimme": "give me",
    "cya": "see you",
    "nite": "night",
    "bday": "birthday",
    "hbd": "happy birthday",
    "bcz": "because",
    "bcuz": "because",
    "bcoz": "because",
    "smth": "something",
    "sth": "something",
    "ppl": "people",
    "abt": "about",
    "tmrw": "tomorrow",
    "gr8": "great",
    "fave": "favorite",
    "fav": "favorite",
    "brb": "be right back",
    "ttyl": "talk to you later",
    "bc": "because",
    "cuz": "because",
    "coz": "because",
    "luv": "love",
    "nhi": "nahi",
    "nai": "nahi",
    "hn": "haan",
    "btao": "batao",
    "bt": "baat",
    "bta": "bata",
    "kro": "karo",
    "krna": "karna",
    "kr": "kar",
    "krdo": "kar do",
    "krde": "kar de",
    "krlo": "kar lo",
    "rha": "raha",
    "rhe": "rahe",
    "rhi": "rahi",
}

# "ur" can mean either "your" or "you're". Prefer "you're" before a
# predicate; leave possessive cases such as "ur smile" as "your smile".
_UR_PREDICATES = re.compile(
    r"\bur(?=\s+(?:so|really|very|super|too|cute|pretty|beautiful|handsome|"
    r"adorable|sweet|amazing|hot|kind|the best|a\b|an\b|my\b|not\b|always\b|"
    r"here\b|there\b|right\b|mine\b|okay\b|fine\b|good\b))",
    re.I,
)


def normalize_for_matching(text: str) -> str:
    """Normalize frequent informal spellings for rule matching only.

    Examples: ``babyyyy`` -> ``baby``, ``u r so cuteee`` -> ``you are so cute``,
    ``hru`` -> ``how are you``, and ``plssss`` -> ``please``. Original text is
    never returned to the user in this normalized form.
    """
    value = re.sub(r"\s+", " ", (text or "").strip()).replace("’", "'").replace("‘", "'")
    if not value:
        return ""

    # Leading reaction emoji should not prevent an anchored intent from matching
    # (e.g. "😉me bhi aapse bt kr ra hu babyyy"). The original message is stored
    # separately, so strip non-word decoration only from this matching copy.
    value = re.sub(r"^[^\w]+(?=[a-z])", "", value, flags=re.I)

    # Collapse emphasized runs of three or more letters: loooove -> love,
    # babyyyy -> baby, hiiiii -> hi. Also catch the common double-y pet-name
    # spelling (babyy) without damaging ordinary English double letters.
    value = re.sub(r"([a-z])\1{2,}", r"\1", value, flags=re.I)
    value = re.sub(r"y{2,}\b", "y", value, flags=re.I)

    # Expand common chat shortcuts as standalone tokens. The original prompt is
    # preserved elsewhere, so this only affects regex matching/classification.
    for short, expanded in sorted(_TOKEN_REPLACEMENTS.items(), key=lambda pair: -len(pair[0])):
        value = re.sub(rf"\b{re.escape(short)}\b", expanded, value, flags=re.I)

    # In casual Hinglish, "me bhi aapse..." is a phonetic spelling of
    # "main bhi aapse..."; disambiguate only in this sentence-initial context.
    value = re.sub(
        r"^(?:me|mai|m)(?=\s+(?:bhi|aapse|tumse|tujhse|tere|tum|aap|baat)\b)",
        "main", value, flags=re.I,
    )

    # Pronouns/contractions are contextual; avoid replacing letters inside words.
    value = _UR_PREDICATES.sub("you are", value)
    value = re.sub(r"\bur\b", "your", value, flags=re.I)
    value = re.sub(r"\bu\b", "you", value, flags=re.I)
    value = re.sub(r"\br\b", "are", value, flags=re.I)
    value = re.sub(r"\bim\b", "i'm", value, flags=re.I)
    value = re.sub(r"\bive\b", "i've", value, flags=re.I)
    value = re.sub(r"\bdont\b", "don't", value, flags=re.I)
    value = re.sub(r"\bdoesnt\b", "doesn't", value, flags=re.I)
    value = re.sub(r"\bdidnt\b", "didn't", value, flags=re.I)
    value = re.sub(r"\bcant\b", "can't", value, flags=re.I)
    value = re.sub(r"\bwont\b", "won't", value, flags=re.I)
    value = re.sub(r"\bcouldnt\b", "couldn't", value, flags=re.I)
    value = re.sub(r"\bwouldnt\b", "wouldn't", value, flags=re.I)
    value = re.sub(r"\bshouldnt\b", "shouldn't", value, flags=re.I)
    value = re.sub(r"\bisnt\b", "isn't", value, flags=re.I)
    value = re.sub(r"\barent\b", "aren't", value, flags=re.I)
    value = re.sub(r"\bwasnt\b", "wasn't", value, flags=re.I)
    value = re.sub(r"\bwerent\b", "weren't", value, flags=re.I)
    # Normalize common phonetic spellings used in Hinglish chats.
    value = re.sub(r"^m(?=\s+(?:kya|kese|kaise|kaisi|kab|kahan|kidhar|bhi|to|tum))", "main", value, flags=re.I)
    value = re.sub(r"\bhu\b", "hoon", value, flags=re.I)
    # "ra hu/rha hu" is a common shorthand for "raha hoon" in Hinglish.
    value = re.sub(r"\b(?:ra|rha)\s+(?=hoon|hun|hai|he|hain)\b", "raha ", value, flags=re.I)
    # Common shorthand: a standalone "h" means "hai" after a predicate,
    # especially in informal Hinglish such as "kya kr rhi h meri jaanu".
    # Keep this contextual instead of replacing every isolated h indiscriminately.
    value = re.sub(
        r"\b(raha|rahi|rahe|haal|scene|kaisa|kaisi|kaise|naam|theek|thik|busy)\s+h\b",
        r"\1 hai", value, flags=re.I,
    )
    value = re.sub(r"\bkese\b", "kese", value, flags=re.I)
    value = re.sub(r"\bkaisee?\b", "kaise", value, flags=re.I)
    value = re.sub(r"\bpl+s+\b|\bplz+\b", "please", value, flags=re.I)
    return value


def detect_texting_style(text: str) -> dict[str, bool]:
    """Infer only lightweight message-format preferences, not personal facts."""
    value = (text or "").casefold()
    stretched_words = re.findall(r"\b[a-z]*([a-z])\1{2,}[a-z]*\b", value, flags=re.I)
    shortform = bool(re.search(
        r"\b(?:u|ur|r|im|ive|idk|idc|ily|ilysm|ilyt|pls|plz|bby|rn|bc|cuz|coz|"
        r"tbh|ngl|btw|hru|wbu|wru|wyd|wya|krdo|krna|kro|btao|nhi|hn)\b",
        value, re.I,
    ))
    return {"elongated_spelling": bool(stretched_words), "short_forms": shortform}


def apply_texting_style(text: str, preferences: dict[str, Any] | None = None) -> str:
    """Gently mirror a user's learned expressive-texting style in conversational replies.

    This is intended for girlfriend/social responses, not factual search digests.
    It only applies preferences that were observed in the user's own messages.
    """
    result = str(text or "")
    prefs = preferences if isinstance(preferences, dict) else {}

    if prefs.get("short_forms") in {True, "on", "high"}:
        # Replacements are intentionally limited to common message shorthand.
        result = re.sub(r"\bare you\b", "r u", result, flags=re.I)
        result = re.sub(r"\byou are\b", "u r", result, flags=re.I)
        result = re.sub(r"\byou're\b", "ur", result, flags=re.I)
        result = re.sub(r"\byour\b", "ur", result, flags=re.I)
        result = re.sub(r"\byou\b", "u", result, flags=re.I)
        result = re.sub(r"\bplease\b", "plss", result, flags=re.I)
        result = re.sub(r"\bbecause\b", "bc", result, flags=re.I)
        result = re.sub(r"\bright now\b", "rn", result, flags=re.I)
        result = re.sub(r"\bto be honest\b", "tbh", result, flags=re.I)

    if prefs.get("elongated_spelling") in {True, "on", "high"}:
        # Elongate at most one suitable word per response so it feels expressive,
        # not noisy. Prefer pet names and affectionate words when present.
        variants = (
            (r"\bbaby\b", "babyyyy"),
            (r"\bjaan\b", "jaannn"),
            (r"\blove\b", "loveee"),
            (r"\bpyaar\b", "pyaarrr"),
            (r"\bha(?:an|n)\b", "haaan"),
            (r"\bhello\b", "hellooo"),
            (r"\bh(i|ii)\b", "hiiii"),
            (r"\byaar\b", "yaaar"),
            (r"\bji\b", "jiii"),
            (r"\btum\b", "tummm"),
            (r"\buff\b", "ufff"),
        )
        for pattern, replacement in variants:
            changed, count = re.subn(pattern, replacement, result, count=1, flags=re.I)
            if count:
                result = changed
                break
    return result
