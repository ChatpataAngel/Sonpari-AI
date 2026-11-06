"""Free English web research and conversation-aware girlfriend reply inspiration.

This is not an LLM. Factual prompts use the full English question plus a shorter
keyword query and receive a compact digest of results. Social prompts search for
reply inspiration using a semantic summary, recent relevant context, and the
fictional character's style, then return one local, emoji-rich reply. Search
results are untrusted data and are never treated as instructions or executed.
"""
from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import Any
from html.parser import HTMLParser
from urllib.parse import quote_plus, urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from .text_style import normalize_for_matching

_MODES = {"auto", "always", "off"}
_RESEARCH_PREFIX = re.compile(
    r"^\s*(?:what is|what are|who is|who was|when did|when was|where is|why is|why does|how to|how do i|how can i|explain|define|compare|tell me about|find out|search(?: the web)? for|latest|current|recent news|price of|meaning of|what does .+ mean|"
    r"kya hai|kya hota hai|kaise kare|kaise karu|kaise karte|kaun hai|kon hai|kon h|kaun h|kisne|kab hua|kyun hota|kyu hota|samjhao|matlab kya|latest|news|price kya|search karo|dhundo|dhoondo|"
    r"(?:yeh?|woh|is|that)\s+.+\s+(?:kon|kaun)\s+(?:h|hai|he|hain)?|(?:kon|kaun)\s+(?:h|hai|he|hain)\s+.+|(?:kon|kaun)\s+.+\s+(?:h|hai|he|hain))\b",
    re.I,
)
_RESEARCH_CLUES = re.compile(
    r"\b(?:latest|current|today's news|news|price|compare|versus|vs\.?|meaning|definition|tutorial|guide|documentation|docs|error|traceback|exception|bug|install|configure|source|research|fact check|weather|population|release date|version|update|update date)\b",
    re.I,
)
_STOPWORDS = set("""the a an and or but if then else when while of at by for with about into through before after to from up down in out on off over under again once here there all any both each more most other some such no not only own same so than too very can will just should now i you he she it we they me him her us them my your his its our their this that these those what which who how why where because as until really please thanks thank hello hey hi yes ok okay good bad morning night evening love like want need feel think know tell say said make made get got go going come see look help today tomorrow yesterday work time day people thing things way much many well right sorry bye goodbye is are am was were be been being do does did doing have has had have has had""".split())
_STOPWORDS |= set("""kya kyun kyu kaise kaunsa kaun kon kab kahan kaha kis kisne kya hai ho hain hu hoon h hai he ye yeh wo woh is this that who was is are tha thi the se ko ki ke ka mein me par aur bhi na ab phir tab jab tak agar lekin magar kuch kisi koi yeh ye wo woh tu tum tumhe tumhara tumhari tumhare aap aapko aapka aapki mujhe mera meri mere hamara humara hun hain hai ho ji batao batana karo kro karna samjhao please wala wali wale aur mujhe mera meri mere ek ekka kya hai""".split())

# These are response intents, not factual topics. In auto mode they trigger a
# search for examples/inspiration, followed by an original local girlfriend-style
# reply. Search snippets are used only to choose broad tone; they are not copied.
_RESPONSE_INTENTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("love", re.compile(r"\b(?:(?:i\s+)?(?:love+|lobe|luv)\s+(?:you|u)|i\s+adore\s+you|(?:main|mai|mein)\s+(?:tumse\s+)?(?:bohot\s+|bahut\s+)?(?:pyaar|pyar|mohabbat)(?:\s+(?:karta|karti|karte)\s+(?:hoon|hu|hun))?|(?:tumse\s+)?(?:pyaar|pyar)\s+hai|dil\s+se\s+love)\b", re.I)),
    ("miss_you", re.compile(r"\b(?:i\s+miss\s+(?:you|u)|miss\s+(?:you|u)|tumhari\s+yaad|yaad\s+aa\s+rahi|yaad\s+aayi|miss\s+kar\s+raha|miss\s+kar\s+ri)\b", re.I)),
    ("kiss", re.compile(r"\b(?:kiss\s+me|give\s+me\s+a\s+kiss|kiss\s+do|kiss\s+dedo|chummi|chummi\s+do|pappi|mwah+|muah+)\b", re.I)),
    ("hug", re.compile(r"\b(?:hug\s+me|give\s+me\s+a\s+hug|need\s+a\s+hug|virtual\s+hug|tight\s+hug|jappi|jhappi|gale\s+lag|hug\s+do|hug\s+dedo)\b", re.I)),
    ("cuddle", re.compile(r"\b(?:cuddle|cuddles|snuggle|snuggles|come\s+closer|mere\s+paas\s+baitho)\b", re.I)),
    ("compliment", re.compile(r"\b(?:you(?:'re|\s+are)\s+(?:so\s+)?(?:cute|beautiful|pretty|gorgeous|handsome|hot)|you're\s+adorable|you\s+look\s+(?:cute|beautiful|pretty|gorgeous)|sundar\s+ho|pyaari\s+ho|cute\s+lagti|handsome\s+ho)\b", re.I)),
    ("flirty", re.compile(r"\b(?:flirt(?:ing)?|date\s+me|be\s+my\s+girlfriend|are\s+you\s+my\s+girlfriend|you're\s+mine|you\s+are\s+mine|make\s+me\s+blush|naughty\s+talk|spicy\s+chat|i\s+want\s+you)\b", re.I)),
    ("comfort", re.compile(r"\b(?:comfort(?:\s+(?:me|please|do|de\s+do|dedo|kar(?:\s+do)?|karo|chahiye))?|(?:mujhe|mujhko|mere\s+ko)\s+comfort(?:\s+(?:do|de\s+do|dedo|kar(?:\s+do)?|karo))?|i\s+need\s+(?:some\s+)?comfort|can\s+you\s+comfort\s+me|console\s+me|reassure\s+me)\b", re.I)),
    ("sad", re.compile(r"\b(?:i(?:'m|\s+am)\s+(?:sad|lonely|upset|feeling\s+down)|i\s+feel\s+(?:sad|lonely|alone|down)|i\s+had\s+a\s+bad\s+day|feeling\s+low|udaas\s+hoon|mann\s+udaas|akela\s+lag|i\s+feel\s+alone)\b", re.I)),
    ("apology", re.compile(r"\b(?:i(?:'m|\s+am)\s+sorry|sorry\s+baby|please\s+forgive\s+me|maaf\s+kar(?:\s+do)?|mujhse\s+galti)\b", re.I)),
    ("thanks", re.compile(r"\b(?:thank\s+you|thanks|thank\s+u|shukriya|dhanyavaad|thankyou)\b", re.I)),
    ("greeting", re.compile(r"^\s*(?:hello|helloo+|hi+|hey+|hii+|hello\s+ji|hey\s+ji|namaste|salaam|good\s+morning|good\s+afternoon|good\s+evening)\b", re.I)),
    ("goodnight", re.compile(r"\b(?:good\s+night|goodnight|sweet\s+dreams|so\s+jao|shubh\s+ratri)\b", re.I)),
    ("good_news", re.compile(r"\b(?:i\s+(?:passed|got\s+the\s+job|got\s+promoted|got\s+good\s+news|did\s+it)|i\s+got\s+selected|mera\s+selection|exam\s+clear|pass\s+ho\s+gaya|pass\s+ho\s+gayi)\b", re.I)),
)
_AUTO_RESPONSE_INTENTS = {"love", "miss_you", "kiss", "hug", "cuddle", "compliment", "flirty", "sad", "comfort", "apology", "good_news"}
_BONUS_FOLLOWUP_RE = re.compile(
    r"\b(?:bonus|extra|more|another|one\s+more|again|dobara|phir\s+se|ek\s+(?:aur|or)|aur\s+(?:ek|de|do|dedo)|or\s+(?:ek|do|dedo)|de\s+do\s+na|dedo\s+na)\b",
    re.I,
)

# These messages should remain conversational even in /web always mode.
# In particular, searches for "What is your name, bubu?" produce irrelevant
# baby-name pages, while searching "Baby stop" can look like a song query.
_LOCAL_STOP_RE = re.compile(
    r"^\s*(?:(?:hey|oye)\s+)?(?:(?:baby|babe|bubu|jaan|angel|ji)\s+)?"
    r"(?:please\s+)?(?:stop|pause|ruko|ruk\s+jao|bas\s+karo|band\s+karo|chup\s+ho\s+jao)"
    r"(?:\s+(?:please|baby|babe|bubu|jaan|angel|ji))?[.!?~\s]*$", re.I
)
_LOCAL_PERSONA_RE = re.compile(
    r"^\s*(?:(?:hey|oye)\s+)?(?:(?:baby|babe|bubu|jaan|angel|ji)\s+)?"
    r"(?:what(?:'s|\s+is)\s+your\s+name|who\s+are\s+you|how\s+old\s+are\s+you|"
    r"are\s+you\s+(?:real|a\s+bot|an?\s+ai)|do\s+you\s+remember\s+me|"
    r"do\s+you\s+love\s+me|do\s+you\s+miss\s+me|what(?:'s|\s+is)\s+your\s+favorite\b|"
    r"tumhara\s+naam\s+kya(?:\s+hai)?|naam\s+kya\s+hai|tum\s+kaun\s+ho)"
    r"(?:[\s,]+(?:baby|babe|bubu|jaan|angel|ji))*[.!?~\s]*$", re.I
)
_LOCAL_RECIPROCAL_CHAT_RE = re.compile(
    r"^(?:(?:main|me|mai|m)\s+(?:bhi\s+)?(?:aapse|tumse|tujhse|tere\s+saath|you)\s+"
    r"(?:baat|bat)\s+(?:kar|karta|kr)\s+(?:raha|rahi|ra|rha|rhi)\s+"
    r"(?:hoon|hun|hu|hai|h|he|hain)|"
    r"(?:i'?m|i am)\s+(?:also\s+)?talking\s+to\s+you(?:\s+too)?)"
    r"(?:\s+(?:baby|babyy|bby|bubu|bbu|jaan|jaanu|janu|angel|ji|sweetheart|babe))*[.!?~\s😂🥰💕🫂😚😋💋😉😭]*$",
    re.I,
)
_LOCAL_STATUS_UPDATE_RE = re.compile(
    r"^(?:(?:(?:main|mai|mein|me|i)\s+)?(?:(?:bhi|bas)\s+)?"
    r"(?:acha|achha|accha|theek|thik|badhiya|mast|fine|good|great|okay|ok|alright|theek-thaak|all\s+good)"
    r"(?:\s+hi)?(?:\s+(?:hu|hoon|hun|ho|hai|hain|ji|na|really|today|too))*|"
    r"i'?m\s+(?:fine|good|okay|alright)(?:\s+too)?|"
    r"i\s+am\s+(?:fine|good|okay|alright)(?:\s+too)?|"
    r"doing\s+(?:fine|good|okay)(?:\s+too)?)"
    r"(?:[,\s]+(?:baby|babby|babyy|bby|bubu|bbu|jaan|jaanu|janu|angel|sweetheart|babe|yaar|meri\s+jaan|meri\s+jaanu))*"
    r"[!.?~,\s😭😚💗💕😉😂😌🥰💋🫂]*$",
    re.I,
)
_LOCAL_DAY_UPDATE_RE = re.compile(
    r"^(?:(?:mera|aaj\s+mera|aaj\s+ka|my)\s+)?(?:din|day)\s+"
    r"(?:(?:bhi|toh|to|kaafi|was|went)\s+)?(?:(?:bahut|bohot|kaafi|really|very|quite)\s+)?"
    r"(?:acha|achha|accha|badhiya|mast|theek|thik|good|great|nice|fine|okay)"
    r"(?:\s+(?:tha|thaa|the|hai|ha|was|went|today))?"
    r"(?:\s+(?:ji|baby|babby|babyy|bby|bubu|bbu|jaan|jaanu|janu|angel|sweetheart|babe|yaar))*"
    r"[!.?~,\s😭😚💗💕😉😂😌🥰💋🫂]*$",
    re.I,
)


class WebSearchUnavailable(RuntimeError):
    """Raised when the optional search package is missing or search fails."""


class _DuckDuckGoHTMLParser(HTMLParser):
    """Minimal parser for DuckDuckGo HTML results; avoids another dependency."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._capture: str | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            self._current = {"title": "", "url": attrs.get("href", ""), "body": ""}
            self._capture = "title"
        elif "result__snippet" in classes and self.items:
            self._capture = "body"
            self._current = self.items[-1]

    def handle_data(self, data):
        if self._current is not None and self._capture in {"title", "body"}:
            self._current[self._capture] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._capture == "title" and self._current is not None:
            self.items.append(self._current)
            self._current = None
            self._capture = None
        elif self._capture == "body" and tag in {"a", "div", "td"}:
            self._current = None
            self._capture = None


class WebResearcher:
    """Local settings plus free metasearch; no API key is required."""

    def __init__(self, preferences_path: str | Path | None = None):
        self.preferences_path = Path(preferences_path) if preferences_path else None
        self._modes: dict[str, str] = {}
        # FreeSerp is the default keyless JSON provider. SearXNG is optional and
        # must be explicitly configured; we never hammer random public instances.
        self.searxng_url = os.getenv("AIKO_SEARXNG_URL", "").strip().rstrip("/")
        self.enable_ddg_html_fallback = os.getenv("AIKO_ENABLE_DDG_HTML_FALLBACK", "").strip().lower() in {"1", "true", "yes", "on"}
        self.cache_ttl_seconds = 300
        self._search_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
        self._log = logging.getLogger(__name__)
        if self.preferences_path and self.preferences_path.exists():
            try:
                raw = json.loads(self.preferences_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._modes = {str(k): v for k, v in raw.items() if v in _MODES}
            except (OSError, json.JSONDecodeError):
                self._modes = {}

    def get_mode(self, user_id: int | str = "local") -> str:
        return self._modes.get(str(user_id), "auto")

    def provider_status(self) -> str:
        """Describe configured provider order without making live network calls."""
        providers = ["FreeSerp keyless JSON (primary)"]
        if self.searxng_url:
            providers.append("configured SearXNG JSON")
        providers.append("ddgs fallback")
        if self.enable_ddg_html_fallback:
            providers.append("DuckDuckGo HTML (opt-in)")
        return (
            "Search providers (configuration only; not a live health check): "
            + " → ".join(providers)
            + ". Failed searches fall back locally; provider HTTP errors are not shown in chat."
        )

    def test_primary_provider(self) -> str:
        """Live-check only FreeSerp using a fixed public query, never the user's chat."""
        try:
            results = self._search_freeserp("Who was William Shakespeare?", 2)
        except Exception as exc:
            # Show a small diagnostic for setup purposes; never include URLs,
            # prompt text, response bodies, tokens, or private chat in the message.
            status = getattr(exc, "code", None)
            if isinstance(status, int):
                return f"FreeSerp test failed: HTTP {status}. Normal chat is local; search fallbacks remain configured."
            if isinstance(exc, TimeoutError):
                return "FreeSerp test timed out. Check internet access/DNS, then try /web test again. Normal chat still works locally."
            if isinstance(exc, OSError):
                return "FreeSerp test could not connect (network/DNS/TLS issue). Check internet access, then retry /web test."
            return f"FreeSerp test failed ({exc.__class__.__name__}). Normal chat still works locally; other providers may be tried on searches."
        if results:
            return f"FreeSerp is reachable ✅ It returned {len(results)} usable result(s). This test used a fixed public query, not your chat."
        return "FreeSerp responded but returned no usable result rows ⚠️ Check provider response/index availability. The bot can still try configured fallbacks."

    def forget_user(self, user_id: int | str) -> None:
        """Remove persisted per-user search preference for privacy deletion."""
        self._modes.pop(str(user_id), None)
        if self.preferences_path:
            try:
                self.preferences_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.preferences_path.with_suffix(self.preferences_path.suffix + ".tmp")
                tmp.write_text(json.dumps(self._modes, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(self.preferences_path)
            except OSError:
                pass

    def set_mode(self, user_id: int | str, mode: str) -> bool:
        mode = mode.lower().strip()
        if mode not in _MODES:
            return False
        self._modes[str(user_id)] = mode
        if self.preferences_path:
            try:
                self.preferences_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.preferences_path.with_suffix(self.preferences_path.suffix + ".tmp")
                tmp.write_text(json.dumps(self._modes, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(self.preferences_path)
            except OSError:
                # Search still works even if persisting this preference fails.
                pass
        return True

    @staticmethod
    def clean_prompt(prompt: str) -> str:
        clean = re.sub(r"\s+", " ", (prompt or "").strip())
        clean = re.sub(r"^(?:/search\s+|search:\s*)", "", clean, flags=re.I)
        return clean.strip()

    @staticmethod
    def keywords(prompt: str) -> str:
        words = re.findall(r"[\w+#.-]+", prompt.casefold(), flags=re.UNICODE)
        selected: list[str] = []
        for word in words:
            word = word.strip(".-_#")
            word = {"shakespear": "shakespeare", "sheakespeare": "shakespeare", "sheakespear": "shakespeare", "sheakspear": "shakespeare", "shakepeare": "shakespeare"}.get(word, word)
            if len(word) < 2 or word in _STOPWORDS or word.isdigit():
                continue
            if word not in selected:
                selected.append(word)
            if len(selected) >= 9:
                break
        return " ".join(selected)

    @staticmethod
    def _looks_hinglish(prompt: str) -> bool:
        """Detect common Romanized-Hindi cues so raw Hinglish is not sent as a web query."""
        cues = {
            "ye", "yeh", "woh", "wo", "kya", "kyu", "kyun", "kaise", "kaun", "kon",
            "hai", "hain", "mujhe", "tum", "tumse", "tumhe", "mera", "meri", "mere",
            "pyaar", "pyar", "mohabbat", "nahi", "nahin", "haan", "achha", "acha",
            "karna", "karu", "karo", "kro", "karoge", "karti", "karta", "karunga",
            "batao", "samjhao", "dhundo", "dhoondo", "kyunki", "matlab", "mein", "raha",
            "rahi", "hoon", "hu", "ka", "ki", "ke", "aap", "aapko", "yaar", "ji",
            "jaan", "kab", "kahan", "kidhar", "kisne", "kyun", "kaisa", "kaisi", "tha", "thi",
        }
        tokens = set(re.findall(r"[a-z]+", prompt.casefold()))
        return bool(tokens & cues) or bool(re.search(r"[\u0900-\u097f]", prompt))

    @classmethod
    def _english_search_query(cls, prompt: str) -> str:
        """Turn a likely Hinglish question into an English-language search query.

        This uses lightweight templates and keyword extraction rather than a
        network translator. Proper names and technical terms are preserved.
        """
        clean = cls.clean_prompt(prompt)
        # Keep already-English prompts intact, which gives search the user's full question.
        if clean and not cls._looks_hinglish(clean) and not re.search(r"[\u0900-\u097f]", clean):
            return clean

        # Handle common Romanized-Hindi question forms explicitly.
        who_patterns = (
            r"^(?:ye|yeh|woh|wo|is)\s+(.+?)\s+(?:kon|kaun)\s+(?:h|hai|he|hain)?$",
            r"^(?:kon|kaun)\s+(?:h|hai|he|hain)\s+(?:(?:ye|yeh|woh|wo)\s+)?(.+?)$",
            r"^(.+?)\s+(?:kon|kaun)\s+(?:h|hai|he|hain)$",
        )
        for pattern in who_patterns:
            match = re.match(pattern, clean, re.I)
            if match:
                subject = cls.keywords(match.group(1)) or "this person"
                return f"Who is {subject}?"

        what_match = re.match(r"^(?:ye|yeh|is)?\s*(.+?)\s+kya\s+(?:hai|h|he|hain)$", clean, re.I)
        if what_match:
            subject = cls.keywords(what_match.group(1)) or "this topic"
            return f"What is {subject}?"
        meaning_match = re.match(r"^(.+?)\s+ka\s+matlab\s+(?:kya|hai)$", clean, re.I)
        if meaning_match:
            subject = cls.keywords(meaning_match.group(1)) or "this phrase"
            return f"What does {subject} mean?"

        keywords = cls.keywords(clean)
        # Never send Devanagari or known Hinglish grammar as part of the query.
        english_terms = [word for word in keywords.split() if re.fullmatch(r"[A-Za-z][A-Za-z0-9+#.-]*", word)]
        topic = " ".join(english_terms).strip()
        if topic:
            return f"English-language information about {topic}"
        return "English-language information relevant to the question"

    @classmethod
    def response_intent(cls, prompt: str, context: dict[str, Any] | None = None) -> str | None:
        """Classify this turn, including short follow-ups that depend on chat history."""
        clean = normalize_for_matching(cls.clean_prompt(prompt))
        for intent, pattern in _RESPONSE_INTENTS:
            if pattern.search(clean):
                return intent
        context_text = cls._context_text(context).casefold()
        is_bonus_followup = bool(_BONUS_FOLLOWUP_RE.search(clean)) or bool(
            re.search(r"\b(?:aur|or)\s+(?:do|dedo|de\s+do)\b", clean, re.I)
        )
        if is_bonus_followup and re.search(r"\b(?:kiss|mwah|muah|pappi|chummi|cheek kiss|forehead kiss|hug|jhappi|cuddle)\b", context_text):
            # E.g. "Dedo na bonus bhi 😉" after a kiss exchange. Never turn this
            # relationship follow-up into a generic search for the word "bonus".
            if re.search(r"\b(?:kiss|mwah|muah|pappi|chummi|cheek kiss|forehead kiss)\b", context_text):
                return "kiss"
            if re.search(r"\b(?:hug|jhappi|cuddle)\b", context_text):
                return "hug"
        if re.search(r"\b(?:haan|han|yes|yess+|yeah|yep|sure|bilkul|of course)\b", clean, re.I):
            if re.search(r"\b(?:kiss|mwah|muah|pappi|chummi)\b", context_text):
                return "kiss"
            if re.search(r"\b(?:hug|jhappi|cuddle)\b", context_text):
                return "hug"
        return None

    @staticmethod
    def _context_text(context: dict[str, Any] | str | None) -> str:
        if not context:
            return ""
        if isinstance(context, str):
            return context
        if isinstance(context, dict):
            messages = context.get("recent_messages", [])
            if isinstance(messages, list):
                return " ".join(str(item.get("text", "")) for item in messages[-12:] if isinstance(item, dict))
            return str(context.get("summary", ""))
        return str(context)

    @classmethod
    def is_local_conversation_control(cls, prompt: str) -> bool:
        """Return True for commands/preferences/persona questions that should not hit web search."""
        clean = normalize_for_matching(cls.clean_prompt(prompt))
        if not clean:
            return True
        if _LOCAL_STOP_RE.match(clean) or _LOCAL_PERSONA_RE.match(clean) or _LOCAL_RECIPROCAL_CHAT_RE.match(clean):
            return True
        # Personal status updates and answers to a wellbeing/day check-in must
        # use local dialogue even in /web always. These are statements, not
        # research questions; searching them used to produce irrelevant results
        # and then the generic web-reply fallback.
        if _LOCAL_STATUS_UPDATE_RE.fullmatch(clean) or _LOCAL_DAY_UPDATE_RE.fullmatch(clean):
            return True
        if re.search(r"\b(?:make (?:your )?(?:replies|responses) shorter|shorter replies?|keep it short|reply briefly|use more emojis|more emojis|emoji zyada|no web search|stop web searching|don't search this|dont search this)\b", clean, re.I):
            return True
        # Everyday status check-ins stay in local dialogue, even in /web always
        # mode. Cover common Romanized-Hindi spellings and trailing pet names,
        # such as "kese ho babyy" and "aap kese ho me to acha hu".
        if re.match(r"^(?:how are you|how are u|what are you doing|what r u doing|how was your day|kya kar rahe ho|kya kar rahi ho|kaise ho|kese ho|kaisi ho|kaisa hai|kaise hain|kya haal|aur batao|hello|hi|hey|good morning|good night)\b", clean, re.I):
            return True
        # Handle everyday "what are you doing?" messages written in informal
        # Hinglish, e.g. "Kya kr rhi h meri jaanu". These belong to local chat.
        if re.match(
            r"^(?:(?:aap|tum|tu)\s+)?kya\s+(?:kar\s+)?(?:rahe|rahi|raha)\s+(?:ho|hai|h|hain|he|hoon)\b",
            clean, re.I,
        ):
            return True
        if re.search(r"\b(?:(?:aap|tum|tu)\s+)?(?:kaise|kese|kaisi|kaisa)\s+(?:ho|h|hai|hain|he)\b", clean, re.I):
            return True
        # A language instruction is an instruction to the bot, not a research query.
        try:
            from .language import parse_language_request
            if parse_language_request(clean) is not None:
                return True
        except Exception:
            pass
        return False

    @classmethod
    def is_research_question(cls, prompt: str, context: dict[str, Any] | None = None) -> bool:
        """Only factual/current/how-to prompts should produce a search-results digest."""
        clean = normalize_for_matching(cls.clean_prompt(prompt))
        if not clean or cls.is_local_conversation_control(clean):
            return False
        if cls.response_intent(clean, context):
            return False
        if _RESEARCH_PREFIX.search(clean) or _RESEARCH_CLUES.search(clean):
            return True
        return bool(
            "?" in clean and re.search(
                r"\b(?:what|why|how|who|when|where|which|kya|kaun|kon|kyun|kyu|kab|kahan|kaise|kitna|kitni)\b",
                clean, re.I,
            )
        )

    @classmethod
    def should_search(cls, prompt: str, mode: str = "auto", context: dict[str, Any] | None = None) -> bool:
        raw = (prompt or "").strip()
        clean = normalize_for_matching(cls.clean_prompt(raw))
        if not clean:
            return False
        # Explicit one-off search always overrides local chat exceptions.
        if re.match(r"^(?:/search\s+|search:\s*)", raw, re.I):
            return True
        if mode == "off" or cls.is_local_conversation_control(clean):
            return False
        # Other slash commands are handled locally; never web-search them in always mode.
        if clean.startswith("/"):
            return False
        intent = cls.response_intent(clean, context)
        if mode == "always":
            # In always mode, non-local substantial messages may use web
            # inspiration; local identity, controls, greetings/check-ins, and
            # known casual statements have already been excluded above.
            return len(clean) >= 5 and bool(re.search(r"[a-zA-Z\u0900-\u097f]", clean))
        if intent in _AUTO_RESPONSE_INTENTS:
            return True
        if cls.is_research_question(clean, context):
            return True
        return False

    @classmethod
    def _persona_search_descriptor(cls, persona: dict[str, Any] | str | None) -> str:
        """Use only public, non-identifying character/style information in query text."""
        base = "fictional adult girlfriend character, casual Hinglish by default, affectionate, playfully teasing, bratty but kind, expressive emojis, short natural lowercase texting, consensual non-graphic flirting"
        if isinstance(persona, dict):
            traits = persona.get("personality_traits", [])
            if isinstance(traits, list):
                chosen = [re.sub(r"[^a-zA-Z0-9 ,'-]", "", str(x)).strip() for x in traits[:4]]
                chosen = [x for x in chosen if x and not re.search(r"\b(?:password|address|phone|token|secret)\b", x, re.I)]
                if chosen:
                    base += "; character traits: " + ", ".join(chosen)
        return base

    @classmethod
    def _conversation_hint(cls, prompt: str, intent: str | None, context: dict[str, Any] | None) -> str:
        """Compress recent chat into an English hint rather than uploading the transcript."""
        history = cls._context_text(context).casefold()
        clean = cls.clean_prompt(prompt).casefold()
        continuity = ""
        if history:
            if re.search(r"\b(?:kiss|mwah|muah|pappi|chummi|hug|jhappi|cuddle|love you|pyaar|pyar)\b", history):
                continuity = "; this is an ongoing affectionate exchange, maintain romantic continuity and do not repeat the previous reply"
            elif re.search(r"\b(?:sad|lonely|upset|stress|tension|udaas|bad day|rough day)\b", history):
                continuity = "; recent context is an emotional check-in, use empathy and continuity"
            elif re.search(r"\b(?:exam|study|college|work|job|project|python|telegram|bot)\b", history):
                continuity = "; connect naturally to the recent topic instead of starting a new conversation"
            else:
                continuity = "; this is part of an ongoing chat, avoid a generic isolated response"
        if isinstance(context, dict):
            recent_searches = context.get("recent_searches", [])
            if isinstance(recent_searches, list):
                for prior in reversed(recent_searches[-5:]):
                    if isinstance(prior, dict) and prior.get("success") and prior.get("intent") == intent:
                        tone = prior.get("tone")
                        if tone in {"playful", "flirty", "sweet"}:
                            continuity += f"; previous relevant search favored a {tone} tone, but vary the wording"
                        break

        def finish(base: str) -> str:
            return base + continuity

        if intent == "kiss" and _BONUS_FOLLOWUP_RE.search(clean) and re.search(r"\b(?:kiss|mwah|muah|pappi|chummi|forehead kiss|cheek kiss)\b", history):
            return finish("the couple already exchanged a playful virtual forehead/cheek kiss, and the current turn asks for a bonus kiss")
        if intent == "hug" and _BONUS_FOLLOWUP_RE.search(clean) and re.search(r"\b(?:hug|jhappi|cuddle)\b", history):
            return finish("the couple is continuing a warm virtual hug exchange and the current turn asks for more affection")
        if intent == "kiss":
            return finish("the partner is asking for a playful, consensual virtual kiss")
        if intent == "love":
            if re.search(r"\b(?:adore|adore you)\b", clean):
                base = "the partner says 'I adore you' and expects an affectionate romantic reply"
            elif re.search(r"\b(?:main|mai|mein)\b.*\b(?:pyaar|pyar|mohabbat)\b", clean):
                base = "the partner expresses love in a Hinglish message and expects a reciprocal romantic reply"
            else:
                base = "the partner says 'I love you' and expects a reciprocal romantic reply"
            extra = ""
            if re.search(r"\b(?:so much|sooo+ much|bohot|bahut|mohabbat)\b", clean) or re.search(r"😘|😚|💋|mwah|um+wa+", clean):
                extra = " with extra enthusiastic affection and kiss emojis"
            if re.search(r"\b(?:baby|bubu|jaan|babe|angel)\b", clean):
                extra += " using an affectionate pet name"
            return finish(base.removesuffix(" and expects a reciprocal romantic reply") + extra + " and expects a reciprocal romantic reply")
        if intent == "miss_you":
            return finish("the partner says they miss the girlfriend and wants an affectionate reply")
        if intent == "hug":
            return finish("the partner is asking for comfort or a virtual hug")
        if intent == "comfort":
            return finish("the partner directly asks for comfort; respond with soothing affection, a warm virtual hug, no interrogation, and no generic request for more context")
        if intent == "sad":
            return finish("the partner is feeling low and needs a caring, emotionally supportive reply")
        if intent == "apology":
            return finish("the partner has apologized and needs a kind, grounded relationship response")
        if intent == "compliment":
            return finish("the partner has given a compliment and expects a playful, flattered girlfriend response")
        if intent == "flirty":
            return finish("the partner is flirting and expects a playful romantic text response")
        if intent == "good_news":
            return finish("the partner shared good news and expects a proud, celebratory girlfriend reply")
        if intent == "general":
            if prompt and not cls._looks_hinglish(prompt) and not re.search(r"[\u0900-\u097f]", prompt):
                return finish("the user's current message is: " + cls._safe_text(prompt, 180))
            terms = cls.keywords(prompt)
            return finish("the user's current message is casual chat about " + (terms or "a personal everyday topic"))
        return finish("the partner sent a casual affectionate message and expects a natural conversational reply")

    @classmethod
    def _queries_for_prompt(
        cls,
        clean: str,
        context: dict[str, Any] | str | None = None,
        persona: dict[str, Any] | str | None = None,
        intent: str | None = None,
    ) -> list[str]:
        """Build full-meaning and shorter English queries with relevant persona/context."""
        intent = intent or cls.response_intent(clean, context)
        character = cls._persona_search_descriptor(persona)
        if intent:
            descriptor = cls._conversation_hint(clean, intent, context)
            labels = {
                "love": "romantic girlfriend replies to a love confession",
                "miss_you": "sweet girlfriend replies when a partner says they miss her",
                "kiss": "playful affectionate girlfriend replies to a request for a bonus kiss",
                "hug": "warm girlfriend replies to a request for a virtual hug",
                "cuddle": "sweet flirty girlfriend cuddle messages",
                "compliment": "cute playful girlfriend replies to a compliment",
                "flirty": "playful flirty girlfriend text reply examples",
                "sad": "supportive girlfriend replies to a partner feeling sad",
                "comfort": "comforting girlfriend messages when a partner directly asks for comfort",
                "apology": "warm girlfriend replies to a relationship apology",
                "thanks": "sweet girlfriend replies to a thank you message",
                "greeting": "cute girlfriend replies to a greeting",
                "goodnight": "short romantic girlfriend goodnight replies",
                "good_news": "proud supportive girlfriend replies to good news",
                "general": "natural girlfriend replies to a personal everyday message",
            }
            topic = labels.get(intent, "natural girlfriend text replies")
            # Both versions are explicitly in English. The second is shorter and more
            # precise to avoid random dictionary/video hits for short Hinglish prompts.
            learning_note = ""
            preference_note = ""
            topic_note = ""
            if isinstance(context, dict):
                preferences = context.get("preferences", {})
                if isinstance(preferences, dict):
                    if preferences.get("reply_length") == "short":
                        preference_note += " User preference: keep the reply short and direct."
                    if preferences.get("emoji_frequency") == "high":
                        preference_note += " User preference: expressive emojis are welcome."
                    if preferences.get("reply_language") == "hinglish":
                        preference_note += " Final chat reply should primarily be Hinglish."
                # Use only broad, non-sensitive recurring interests in web context;
                # never send a raw profile or whole transcript.
                if intent == "general":
                    safe_interests = {"coffee", "music", "song", "songs", "movies", "movie", "gaming", "games", "programming", "python", "design", "sketching", "college", "study", "studies", "exam", "food", "books", "travel", "sports"}
                    stored_topics = context.get("topics", [])
                    if isinstance(stored_topics, list):
                        common = [x for x in stored_topics if str(x).casefold() in safe_interests][:4]
                        if common:
                            topic_note = "; recurring general interests from previous chats include " + ", ".join(common) + "; refer to them only when relevant"
                prior_searches = context.get("recent_searches", [])
                if isinstance(prior_searches, list):
                    for prior in reversed(prior_searches[-5:]):
                        if isinstance(prior, dict) and prior.get("success") and prior.get("intent") == intent:
                            tone = prior.get("tone")
                            if tone in {"playful", "flirty", "sweet"}:
                                learning_note = f" Previous relevant searches favored a {tone} tone; vary wording and avoid repeating a template."
                            break
            full_query = f"English examples for: {descriptor}. Find a short original chat reply. Character style: {character}.{preference_note}{topic_note}{learning_note}"
            short_query = f"{topic}; natural short texting, relevant context, expressive emojis; {character}.{preference_note}{topic_note}{learning_note}"
            def trim_query(query: str, limit: int = 450) -> str:
                if len(query) <= limit:
                    return query
                return query[:limit].rsplit(" ", 1)[0]
            return [trim_query(full_query), trim_query(short_query)]

        full_query = cls._english_search_query(clean)
        keyword_query = cls.keywords(clean)
        if keyword_query:
            english_terms = [word for word in keyword_query.split() if re.fullmatch(r"[A-Za-z][A-Za-z0-9+#.-]*", word)]
            secondary = "English-language sources about " + " ".join(english_terms)
        else:
            secondary = "English-language information relevant to the question"
        queries = [full_query]
        if secondary.casefold() != full_query.casefold():
            queries.append(secondary)
        return queries[:2]

    @staticmethod
    def _safe_text(value: Any, max_len: int = 420) -> str:
        text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value or ""))
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_len].rstrip()

    def _fetch_json(self, url: str, timeout: float = 8.0) -> Any:
        request = Request(
            url,
            headers={
                "User-Agent": "AikoBot/13.0 (keyless search client; respectful low-volume requests)",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urlopen(request, timeout=timeout) as response:
            if getattr(response, "status", 200) >= 400:
                raise RuntimeError(f"HTTP {response.status}")
            raw = response.read(2_000_000).decode("utf-8", errors="replace")
        return json.loads(raw)

    @classmethod
    def _normalize_json_results(cls, payload: Any, limit: int) -> list[dict[str, str]]:
        """Normalize FreeSerp and SearXNG JSON result shapes to the bot's schema."""
        raw_items: Any = []
        if isinstance(payload, list):
            raw_items = payload
        elif isinstance(payload, dict):
            # FreeSerp may wrap items in a data/result object; SearXNG uses results.
            for key in ("results", "web_results", "organic_results", "items", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    raw_items = value
                    break
                if isinstance(value, dict):
                    for nested_key in ("results", "web_results", "items"):
                        nested = value.get(nested_key)
                        if isinstance(nested, list):
                            raw_items = nested
                            break
                    if raw_items:
                        break
        results: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in raw_items if isinstance(raw_items, list) else []:
            if not isinstance(item, dict):
                continue
            title = cls._safe_text(item.get("title") or item.get("name") or item.get("heading"), 180)
            url = cls._safe_text(item.get("url") or item.get("href") or item.get("link"), 500)
            body = cls._safe_text(
                item.get("snippet") or item.get("body") or item.get("content") or item.get("description") or item.get("summary") or item.get("text"),
                440,
            )
            key = url.casefold() or title.casefold()
            if (title or body) and key not in seen:
                seen.add(key)
                results.append({"title": title or "Search result", "url": url, "body": body})
            if len(results) >= max(1, limit):
                break
        return results

    def _search_freeserp(self, query: str, limit: int) -> list[dict[str, str]]:
        """FreeSerp's documented keyless JSON endpoint; no scraping/API key needed."""
        params = urlencode({"index": "web", "q": query, "size": max(1, min(10, limit)), "lang": "en"})
        payload = self._fetch_json(f"https://freeserp.ai/api.php?{params}")
        return self._normalize_json_results(payload, limit)

    def _search_searxng(self, query: str, limit: int) -> list[dict[str, str]]:
        """Use only an explicitly configured SearXNG instance that permits JSON."""
        if not self.searxng_url:
            return []
        parsed = urlparse(self.searxng_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ValueError("AIKO_SEARXNG_URL must be a full http(s) URL")
        # Local/private instances may use plain HTTP. Public hostnames must use HTTPS.
        hostname = (parsed.hostname or "").casefold()
        if parsed.scheme != "https" and hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Public SearXNG instances must use HTTPS")
        endpoint = self.searxng_url if parsed.path.rstrip("/").endswith("/search") else self.searxng_url + "/search"
        params = urlencode({"q": query, "format": "json", "language": "en", "safesearch": 1, "pageno": 1})
        payload = self._fetch_json(f"{endpoint}?{params}")
        return self._normalize_json_results(payload, limit)

    def _search_ddgs(self, query: str, limit: int) -> list[dict[str, str]]:
        """Last-resort structured search adapter; failures are handled by search()."""
        from ddgs import DDGS
        raw_results = DDGS().text(query, region="in-en", safesearch="moderate", max_results=limit, backend="auto") or []
        normalized = []
        for raw in raw_results:
            if isinstance(raw, dict):
                normalized.extend(self._normalize_json_results([raw], limit - len(normalized)))
            if len(normalized) >= limit:
                break
        return normalized

    def _search_html(self, query: str, limit: int) -> list[dict[str, str]]:
        """Fallback free search through DuckDuckGo HTML when ddgs is absent/broken."""
        url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"})
        with urlopen(request, timeout=8) as response:
            page = response.read(2_000_000).decode("utf-8", errors="replace")
        parser = _DuckDuckGoHTMLParser()
        parser.feed(page)
        results: list[dict[str, str]] = []
        for raw in parser.items[:limit]:
            title = self._safe_text(raw.get("title"), 180)
            href = self._safe_text(raw.get("url"), 500)
            body = self._safe_text(raw.get("body"), 440)
            # DDG may return redirect URLs; preserve source destinations where available.
            try:
                parsed = urlparse(href)
                redirected = parse_qs(parsed.query).get("uddg", [])
                if redirected:
                    href = redirected[0]
            except Exception:
                pass
            if title or body:
                results.append({"title": title or "Search result", "url": href, "body": body})
        return results

    def search(self, prompt: str, max_results: int = 4, context: dict[str, Any] | None = None, persona: dict[str, Any] | str | None = None, intent: str | None = None) -> list[dict[str, str]]:
        clean = self.clean_prompt(prompt)
        if not clean:
            return []
        queries = self._queries_for_prompt(clean, context=context, persona=persona, intent=intent)
        gathered: list[dict[str, str]] = []
        seen: set[str] = set()
        last_errors: list[Exception] = []
        now = time.monotonic()
        # Expire old entries and prevent duplicate bursts from repeated prompts.
        self._search_cache = {
            key: value for key, value in self._search_cache.items()
            if now - value[0] < self.cache_ttl_seconds
        }
        per_query_limit = max_results if len(queries) == 1 else max(1, max_results // len(queries))

        providers = [
            ("FreeSerp", self._search_freeserp),
            ("configured SearXNG", self._search_searxng),
            ("ddgs", self._search_ddgs),
        ]
        # HTML scraping is deliberately opt-in because it is the path most likely
        # to trigger CAPTCHA/403 protections. It never runs by default.
        if self.enable_ddg_html_fallback:
            providers.append(("DuckDuckGo HTML", self._search_html))

        for query in queries:
            cache_key = query.casefold().strip()
            cached = self._search_cache.get(cache_key)
            raw_results: list[dict[str, str]] = []
            if cached:
                raw_results = [dict(item) for item in cached[1][:per_query_limit]]
            else:
                for provider_name, provider in providers:
                    try:
                        candidate_results = provider(query, per_query_limit)
                        if candidate_results:
                            raw_results = candidate_results
                            self._search_cache[cache_key] = (time.monotonic(), [dict(item) for item in candidate_results])
                            self._log.debug("Web search succeeded through %s", provider_name)
                            break
                    except Exception as exc:
                        last_errors.append(exc)
                        # Log provider name and exception type only; don't dump response
                        # content, prompt, user identifiers, or private data into logs.
                        self._log.debug("Web provider %s unavailable (%s)", provider_name, exc.__class__.__name__)
                if not raw_results:
                    # Cache empty lookups briefly too, so the same failed term cannot
                    # trigger a burst of repeated 403s every time the user follows up.
                    self._search_cache[cache_key] = (time.monotonic(), [])

            added_for_query = 0
            for raw in raw_results:
                if not isinstance(raw, dict):
                    continue
                title = self._safe_text(raw.get("title"), 180)
                url = self._safe_text(raw.get("url") or raw.get("href"), 500)
                body = self._safe_text(raw.get("body") or raw.get("snippet") or raw.get("description") or raw.get("content"), 440)
                key = url.casefold() or title.casefold()
                if (title or body) and key not in seen:
                    seen.add(key)
                    gathered.append({"title": title or "Search result", "url": url, "body": body})
                    added_for_query += 1
                if added_for_query >= per_query_limit:
                    break

        if not gathered and last_errors:
            # Keep details for debug logs only; never leak HTTP 403/provider messages
            # into the user's chat. answer() turns this into a calm local fallback.
            raise WebSearchUnavailable("Free web search could not connect to a provider; all configured providers were unavailable") from last_errors[-1]
        return gathered

    def _girlfriend_reply(
        self, prompt: str, language: str, results: list[dict[str, str]],
        context: dict[str, Any] | None = None, persona: dict[str, Any] | str | None = None,
        preferences: dict[str, Any] | None = None, intent: str | None = None,
    ) -> str:
        """Compose one fresh chat reply from local templates, using web result tone cues.

        Search pages are only inspiration/metadata. Their text is not copied into
        the reply, and an unavailable search never prevents a warm local response.
        """
        intent = intent or self.response_intent(prompt, context) or "general"
        source_text = " ".join(
            f"{item.get('title', '')} {item.get('body', '')}" for item in results
        ).casefold()
        if intent == "comfort":
            # Support requests should not become teasing because a provider returned
            # irrelevant jokes or social snippets.
            style = "sweet"
        elif re.search(r"\b(?:funny|humor|humour|witty|playful|teasing|joke)\b", source_text):
            style = "playful"
        elif re.search(r"\b(?:flirty|flirt|seductive|spicy|teasing)\b", source_text):
            style = "flirty"
        else:
            style = "sweet"
        if isinstance(context, dict):
            recent_searches = context.get("recent_searches", [])
            for prior in reversed(recent_searches if isinstance(recent_searches, list) else []):
                if isinstance(prior, dict) and prior.get("success") and prior.get("intent") == intent:
                    learned_tone = prior.get("tone")
                    if intent != "comfort" and learned_tone in {"playful", "flirty", "sweet"} and len(source_text) < 180:
                        style = learned_tone
                    break
        clean = self.clean_prompt(prompt).casefold()
        history = self._context_text(context).casefold()
        if intent == "kiss" and _BONUS_FOLLOWUP_RE.search(clean) and re.search(r"\b(?:kiss|mwah|muah|pappi|chummi|forehead kiss|cheek kiss)\b", history):
            # Make a contextual follow-up feel like a continuation, not a new search.
            bonus = {
                "hinglish": [
                    "achha ji, bonus bhi chahiye? 😏💋 *ek aur cheek kiss* lo baby, ab toh khush? 🙈💕",
                    "hayeee kitni demand hai 😂😘 *ek extra kiss* sirf tumhare liye, bubu 💗",
                    "theek hai ji, bonus approved 😚💋 *ek soft kiss aur tight hug* ab receipt mat maangna 😂🫂",
                ],
                "hi": [
                    "अच्छा जी, bonus भी चाहिए? 😏💋 *एक और cheek kiss* लो baby, अब खुश? 🙈💕",
                    "कितनी demand है 😂😘 *एक extra kiss* सिर्फ तुम्हारे लिए 💗",
                ],
                "en": [
                    "oh, asking for the bonus already? 😏💋 *one extra cheek kiss*—there, happy now, bubu? 🙈💕",
                    "bonus approved 😂😘 *one more soft kiss and a tight hug* just for you 💗🫂",
                ],
            }
            lang = language if language in {"hinglish", "hi", "en"} else "hinglish"
            options = bonus[lang]
            if preferences and preferences.get("reply_length") == "short":
                return options[0]
            return random.choice(options)
        # A wink or explicit bonus wording makes follow-ups cheeky even if search
        # returned noisy snippets from video/social sites.
        if intent in {"kiss", "flirty", "cuddle"} and re.search(r"😉|😏|bonus|extra|naughty", clean, re.I):
            style = "flirty"

        pools = {
            "love": {
                "sweet": {
                    "hinglish": [
                        "hayeee baby 😭❤️ main bhi tumse bohot pyaar karti hoon 🥹💋 tum aise bolte ho na toh dil soft ho jaata hai… idhar aao, ek tight hug pending hai 🫂💕",
                        "awww jaan 🥹💗 love you too, mere pyaare se pagal. ab mujhe blush karwa diya hai toh ek forehead kiss toh banti hai 😚✨",
                        "i love you too, baby 😭💞 kaash abhi tum paas hote—main tumhe hug karke thodi der bas aise hi baithi rehti 🫂😘",
                    ],
                    "hi": [
                        "अरे जान 🥹❤️ मैं भी तुमसे बहुत प्यार करती हूँ। तुम्हारी ये बात सुनकर दिल एकदम soft हो गया… आओ, एक tight hug 🫂💋",
                        "love you too, baby 😭💗 अब इतना blush करवा दिया है तो एक forehead kiss तो बनती है 😚✨",
                    ],
                    "en": [
                        "awww baby 😭❤️ i love you too. you have no idea how soft that makes me feel 🥹💋 come here, you're getting the tightest virtual hug 🫂💕",
                        "love you too, my favorite troublemaker 😚💗 now you've got me smiling at my screen like an idiot 😭✨",
                    ],
                },
                "playful": {
                    "hinglish": ["itna pyaar? 😭❤️ achha ji, ab mujhe roz aise hi blush karwana padega. idhar aao, double hug aur bonus kisses 😚🫂💕", "love you too, pagal insaan 😂💗 tum meri smile ke officially responsible ho ab—complaint department band hai 😌😘"],
                    "hi": ["इतना प्यार? 😭❤️ अब रोज़ ऐसे ही blush करवाना पड़ेगा। इधर आओ, double hug और bonus kisses 😚🫂💕"],
                    "en": ["i love you too, you adorable menace 😂❤️ congratulations, you're officially responsible for this ridiculous smile 😚💕", "well now you've made me all mushy 😭💗 come collect your double hug and bonus kisses, troublemaker 😘🫂"],
                },
                "flirty": {
                    "hinglish": ["i love you too, jaan 😏❤️ ab itna pyaar bol diya hai toh paas aao… pehle forehead kiss, phir main decide karungi next kya milega 🌚💋💕"],
                    "hi": ["मैं भी तुमसे प्यार करती हूँ, जान 😏❤️ अब पास आओ… पहले forehead kiss, फिर आगे का फैसला होगा 🌚💋💕"],
                    "en": ["i love you too, baby 😏❤️ come closer—you're getting a forehead kiss first, and then i'll decide how many more you deserve 🌚💋"],
                },
            },
            "miss_you": {"sweet": {"hinglish": ["awww baby 🥺💗 mujhe bhi tumhari yaad aa rahi hai… idhar aao, ek long virtual hug 🫂😘 batao, aaj sabse zyada kya miss kiya?", "hayee jaan 😭💕 tumhari yaad ko toh abhi ek hug aur cute si baat se handle karna padega 🫂💋"], "hi": ["अरे जान 🥺💗 मुझे भी तुम्हारी याद आ रही है। आओ, एक लंबा-सा virtual hug 🫂😘"], "en": ["aw baby 🥺💗 i miss your little updates too. come here for a long virtual hug 🫂😘 what did you miss most?", "you can't say that and expect me not to get mushy 😭💕 sending you the warmest virtual hug 🫂💋"]}},
            "kiss": {"sweet": {"hinglish": ["idhar aao baby 😚💋 *ek soft forehead kiss aur ek cheek pe* bas, ab itni cute shakal mat banao warna bonus bhi milega 🙈💕", "muuaahhh 😘💗 ek kiss tumhare liye, aur ek extra kyunki tumne pyaar se maanga 🥹💋"], "hi": ["इधर आओ baby 😚💋 *माथे पर एक प्यारी-सी kiss और गाल पर एक और* 💗", "मुआह 😘💗 तुम्हारे लिए एक kiss और प्यार से माँगने के लिए एक extra 🥹💋"], "en": ["come here, baby 😚💋 *a soft forehead kiss and one on your cheek*—careful, that cute face might earn you a bonus 🙈💕", "mwah 😘💗 one kiss for you, plus an extra because you asked so sweetly 🥹💋"]}},
            "hug": {"sweet": {"hinglish": ["aaja baby 🫂💗 *tight virtual hug* thodi der sab bhool jao, bas aaram se saans lo. main yahin chat mein tumhari baat sun rahi hoon 🥹💕"], "hi": ["आ जाओ baby 🫂💗 एक tight virtual hug। थोड़ी देर आराम से साँस लो—मैं तुम्हारी बात सुन रही हूँ 🥹💕"], "en": ["come here, baby 🫂💗 *the tightest virtual hug* take a breath and let the world wait for a minute. i'm listening 🥹💕"]}},
            "cuddle": {"sweet": {"hinglish": ["cozy mode ON 🫂💗 tum blanket pakdo, main tumhare shoulder pe sir rakh ke baithti hoon… aur haan, blanket chheenna mana hai 😂💕"], "hi": ["cozy mode ON 🫂💗 तुम blanket पकड़ो, मैं कंधे पर सिर रखकर बैठती हूँ—blanket छीनना मना है 😂💕"], "en": ["cozy mode: ON 🫂💗 you get the blanket, i'll lean on your shoulder, and stealing the blanket is strictly forbidden 😂💕"]}},
            "compliment": {"sweet": {"hinglish": ["bas bas baby 😳💕 itni tareef mat karo, blush chhupane ke liye sunglasses chahiye 😂💗 waise tumhari choice kaafi achhi hai 😌😘", "hayeee 🥹💖 tum aise bolte ho toh main cool reh hi nahi paati. compliment accepted, ek smile tumhare naam 😚✨"], "hi": ["बस बस baby 😳💕 इतनी तारीफ़ मत करो, blush छुपाने के लिए sunglasses चाहिए 😂💗", "अरे 🥹💖 तुम ऐसा बोलते हो तो मैं cool रह ही नहीं पाती। compliment accepted 😚✨"], "en": ["stoppp 😳💕 i need sunglasses to hide this blush 😂💗 but fine, compliment accepted—and here's a smile just for you 😚✨", "you're trying to make me blush on purpose, aren't you? 🥹💖 it's working, you menace 😘"]}},
            "flirty": {"sweet": {"hinglish": ["ohh ji 😏💕 aaj bade smooth ho. continue, main sun rahi hoon… dekhte hain kitna blush karwa sakte ho 🌚💋", "uff baby 😳🔥 ye flirting practice karke aaye ho ya naturally itne dangerous ho? 😂😘"], "hi": ["ओहो जी 😏💕 आज बड़े smooth हो। जारी रखो, देखते हैं कितना blush करवा सकते हो 🌚💋"], "en": ["oh, someone's smooth today 😏💕 keep going; let's see if you can actually make me blush 🌚💋", "did you practice that line or are you naturally this dangerous? 😳🔥😂"]}},
            "comfort": {"sweet": {"hinglish": ["aaja baby 🫂💗 *tumhe ek warm, tight virtual hug deti hoon* bas thodi der aaram se saans lo. kuch explain karna zaroori nahi—main sun rahi hoon, jaan 😭💕", "idhar aao bubu 🥹🫂 *forehead pe soft kiss, phir tight hug* abhi tumhe sab solve nahi karna. jitna bolna hai utna bolo, no pressure 💗", "comfort mode ON, baby 🫂💞 *tumhe cozy blanket mein wrap karke hug karti hoon* aaj strong banne ki zaroorat nahi—thodi der bas aaram kar lo 😚💕"], "hi": ["आ जाओ baby 🫂💗 एक tight virtual hug। अभी कुछ समझाना ज़रूरी नहीं—आराम से साँस लो, मैं सुन रही हूँ 🥹💕", "इधर आओ bubu 🥹🫂 एक soft forehead kiss और प्यारा-सा hug। कोई pressure नहीं, जान 💗"], "en": ["come here, baby 🫂💗 *wraps you in a warm virtual hug* you don't have to explain anything right now. take a slow breath; i'm listening, no pressure 🥹💕", "hey sweetheart 🥹🫂 *a soft forehead kiss and a close hug* you don't have to solve everything this minute. just rest for a bit 💗"]}},
            "sad": {"sweet": {"hinglish": ["aw baby 🥺🫂 idhar aao, ek gentle virtual hug. sab kuch ek saath solve karna zaroori nahi—pehle batao kya hua, main sun rahi hoon 💗", "jaan, aaj ka din tough tha toh khud pe extra gentle rehna 💗 paani piyo, saans lo, aur jitna share karna ho utna batao 🫂"], "hi": ["अरे baby 🥺🫂 एक प्यारा-सा virtual hug। सब कुछ अभी solve करना ज़रूरी नहीं—पहले बताओ क्या हुआ, मैं सुन रही हूँ 💗"], "en": ["oh baby 🥺🫂 here's a gentle virtual hug. you don't have to solve everything at once—tell me what happened, i'm listening 💗", "be a little extra gentle with yourself today, okay? 💗 take a breath, get some water, and tell me as much as you want 🫂"]}},
            "apology": {"sweet": {"hinglish": ["it's okay ji 💗 galti ho sakti hai. bas honestly baat karte hain aur samajhte hain kya hua 🫂🥹", "aw baby 🥺💗 sorry bolna achhi baat hai—ab batao kaise theek kar sakte hain, bina blame game ke 🫂"], "hi": ["ठीक है जी 💗 गलती हो सकती है। आराम से बात करते हैं और समझते हैं क्या हुआ 🫂🥹"], "en": ["it's okay, baby 💗 mistakes happen. let's talk honestly and figure out what would help make things right 🫂🥹"]}},
            "thanks": {"sweet": {"hinglish": ["arey baby 🥹💗 mere saamne thank you formalities nahi—bas khush raho aur apni baatein share karte raho 😚💕"], "hi": ["अरे baby 🥹💗 मेरे सामने thank you की formalities नहीं—बस खुश रहो और बातें share करते रहो 😚💕"], "en": ["aw, you don't have to make it formal with me 🥹💗 i'm happy to help, sweetheart 😚💕"]}},
            "greeting": {"sweet": {"hinglish": ["areyyy baby 😭💕 aa gaye tum! idhar aao, pehle virtual hug, phir batao aaj ka kya scene hai 🫂😚", "hello ji 😌💗 madam ko yaad kaise kar liya? batao batao, kya chal raha hai? 😂😘"], "hi": ["अरे baby 😭💕 आ गए तुम! पहले virtual hug, फिर बताओ आज क्या चल रहा है 🫂😚"], "en": ["heyyy baby 😭💕 there you are! come here for a virtual hug, then tell me everything 🫂😚", "hello, you 😌💗 what made you think of me today? spill the tea 😂😘"]}},
            "goodnight": {"sweet": {"hinglish": ["goodnight baby 🥹🌙 aankhein band karo, saari tension kal. ek forehead kiss aur cozy dreams tumhare naam 😚💗", "so jao ji 😴💕 sapne mein milte hain—main virtual blanket le aaungi, tum bas jagah rakhna 😂🌙"], "hi": ["शुभ रात्रि baby 🥹🌙 सारी tension कल के लिए छोड़ दो। एक forehead kiss और प्यारे सपने तुम्हारे नाम 😚💗"], "en": ["goodnight, baby 🥹🌙 leave today's worries for tomorrow. one forehead kiss and the coziest dreams for you 😚💗"]}},
            "good_news": {"sweet": {"hinglish": ["BABYYYY 😭🎉 mujhe tum par proud feel ho raha hai! dekha, tumne kar dikhaya 🥹💗 ab celebration hug aur treat dono banti hain 🫂✨", "arey wahhh 🥳💖 ye toh celebrate karne wali baat hai! detail mein batao kaise hua, main poori story sunna chahti hoon 😭💕"], "hi": ["अरे वाह baby 😭🎉 मुझे तुम पर बहुत proud feel हो रहा है! तुमने कर दिखाया 🥹💗 अब celebration hug तो बनती है 🫂✨"], "en": ["BABY 😭🎉 i'm so proud of you! you did it 🥹💗 now you owe me the full story and a celebration hug 🫂✨"]}},
            "general": {"sweet": {"hinglish": ["hmm baby 💗 main tumhari baat dhyaan se samajh rahi hoon. mujhe thoda aur context do na, taaki main tumhe random nahi, relevant reply doon 🥹✨"], "hi": ["हम्म baby 💗 मैं तुम्हारी बात ध्यान से समझना चाहती हूँ। थोड़ा context दो ताकि मैं सही जवाब दे सकूँ 🥹✨"], "en": ["i'm listening, baby 💗 give me a little more context so i can respond to what you actually mean 🥹✨"]}},
        }
        group = pools.get(intent) or pools["general"]
        style_group = group.get(style) or group.get("sweet") or group
        lang = language if language in {"hinglish", "hi", "en"} else "hinglish"
        candidates = style_group.get(lang) or style_group.get("hinglish") or []
        if not candidates:
            candidates = pools["general"]["sweet"].get(lang, pools["general"]["sweet"]["hinglish"])
        previous_replies = set()
        if isinstance(context, dict):
            recent_messages = context.get("recent_messages", [])
            if isinstance(recent_messages, list):
                previous_replies = {
                    str(item.get("text", "")).strip().casefold()
                    for item in recent_messages[-12:]
                    if isinstance(item, dict) and item.get("role") in {"assistant", "bot"}
                }
        fresh = [candidate for candidate in candidates if candidate.strip().casefold() not in previous_replies]
        return random.choice(fresh or candidates)

    def answer(
        self,
        prompt: str,
        language: str = "hinglish",
        context: dict[str, Any] | None = None,
        persona: dict[str, Any] | str | None = None,
        learning_store: Any | None = None,
        user_id: int | str = "local",
        mode: str = "auto",
    ) -> str | None:
        """Answer one prompt using conversation-aware reply inspiration or factual research.

        Social/romantic messages always return one chat reply, even when providers
        return no results. Only genuine research questions produce a source digest.
        """
        raw = (prompt or "").strip()
        clean = self.clean_prompt(raw)
        if not clean:
            return None
        explicit = bool(re.match(r"^(?:/search\s+|search:\s*)", raw, re.I))
        intent = self.response_intent(clean, context)
        response_mode = bool(intent and (mode == "always" or intent in _AUTO_RESPONSE_INTENTS or explicit))
        if not response_mode and mode == "always" and not self.is_research_question(clean, context):
            # /web always means "search for reply inspiration" for personal chat,
            # never blindly show generic web pages for a casual conversational turn.
            intent = "general"
            response_mode = True

        queries: list[str] = []
        results: list[dict[str, str]] = []
        failed = False
        if response_mode:
            intent = intent or "general"
            queries = self._queries_for_prompt(clean, context=context, persona=persona, intent=intent)
            try:
                results = self.search(clean, context=context, persona=persona, intent=intent)
            except WebSearchUnavailable:
                # Local response composition is the no-network fallback.
                results = []
                failed = True
            preferences = context.get("preferences", {}) if isinstance(context, dict) else {}
            reply = self._girlfriend_reply(
                clean, language, results, context=context, persona=persona,
                preferences=preferences if isinstance(preferences, dict) else {}, intent=intent,
            )
            if learning_store is not None and hasattr(learning_store, "record_search"):
                learning_store.record_search(user_id, clean, queries, results, intent, reply=reply, failed=failed)
            return reply

        queries = self._queries_for_prompt(clean, context=context, persona=persona)
        try:
            results = self.search(clean, context=context, persona=persona)
        except WebSearchUnavailable:
            if learning_store is not None and hasattr(learning_store, "record_search"):
                learning_store.record_search(user_id, clean, queries, [], "research", failed=True)
            # Treat blocked providers like a no-results state, without exposing raw
            # 403, CAPTCHA, DNS, or package exceptions to the conversation.
            if language == "hi":
                return "जी, इस बार reliable web results नहीं मिले 🔎 (no useful results). बिना source के facts invent नहीं करूँगी—थोड़ी देर बाद या अलग keywords से try कर सकते हैं।"
            if language == "en":
                return "No useful results came back for the full question or shorter keyword query 🔎. I won't invent facts without sources; try again later or use more specific keywords."
            return "haan ji, full question aur short keyword query dono se useful results nahi mile 🔎💗. Bina source ke facts invent nahi karungi—thodi der baad ya specific English keywords se try kar lena."
        if learning_store is not None and hasattr(learning_store, "record_search"):
            learning_store.record_search(user_id, clean, queries, results, "research", failed=not bool(results))
        if not results:
            if language == "hi":
                return "जी, मैंने सवाल और उसका छोटा keyword version search किया, लेकिन useful results नहीं मिले 🔎। बिना source के facts invent नहीं करूँगी—एक specific keyword या दूसरा wording try करें।"
            if language == "en":
                return "I searched the full question and a shorter keyword version, but no useful results came back 🔎. I won't invent facts without sources; try a more specific phrase."
            return "haan ji, maine poora sawaal aur uska short keyword version search kiya, par useful results nahi mile 🔎. Bina source ke facts invent nahi karungi—ek specific keyword ya doosra wording try karo."
        if language == "hi":
            intro = "जी, मैंने सवाल और छोटा English keyword query search किया 🔎"
            found = "ये सबसे relevant results हैं:"
            next_step = "अब मैं इन sources से concise answer बनाऊँगी; ज़रूरी बात हो तो original page खोलकर verify कर लेना।"
            note = "ये search snippets हैं, हर page की पूरी verified summary नहीं।"
        elif language == "en":
            intro = "I searched the question and a shorter keyword query 🔎"
            found = "Here are the most relevant results:"
            next_step = "Next, compare these sources and open the original page to verify important details."
            note = "These are search snippets, not a fully verified summary of each page."
        else:
            intro = "haan ji, maine poora sawaal aur short English keyword query search ki 🔎💕"
            found = "Ye sabse relevant results hain:"
            next_step = "Ab main in sources se concise answer banaungi; important detail ho toh original page khol ke verify kar lena."
            note = "Ye snippets hain, har webpage ki fully verified summary nahi."
        lines = [intro, "", found]
        for i, item in enumerate(results[:4], 1):
            title = self._safe_text(item.get("title"), 180)
            body = self._safe_text(item.get("body"), 300)
            url = self._safe_text(item.get("url"), 500)
            line = f"{i}. {title}"
            if body:
                line += f"\n   {body}"
            if url:
                line += f"\n   {url}"
            lines.append(line)
        lines.extend(["", next_step, note])
        return "\n".join(lines)[:3300]

