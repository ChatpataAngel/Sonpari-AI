"""Universal text translation for Aiko, using keyless web services.

This is a translation utility, not a conversational AI/model. It makes requests
only when the user explicitly asks to translate or run a translation test.
Normal girlfriend chat is never sent to the translation providers automatically.

Providers:
1. An optional LibreTranslate-compatible endpoint supplied by AIKO_TRANSLATE_URL.
2. Google's public translate.googleapis.com web endpoint (unofficial; may throttle
   or change, so failure is handled quietly and cached results remain usable).

No API key is required by the default Google endpoint. A configured LibreTranslate
server may enforce its own key or rate-limit policy; this client does not require
or send a key.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import json
import logging
import os
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

_LOG = logging.getLogger(__name__)
_TIMEOUT_SECONDS = 8
_MAX_CHARACTERS = 4500
_CACHE_SIZE = 256
_CACHE_TTL = 600
_USER_AGENT = "AikoBot-UniversalTranslator/1.0 (keyless translation client)"

# Widely used names and aliases. Any valid-looking provider language code is
# also accepted, so users are not restricted to this display list.
_LANGUAGE_ALIASES: dict[str, str] = {
    "auto": "auto", "detect": "auto",
    "afrikaans": "af", "albanian": "sq", "amharic": "am", "arabic": "ar",
    "armenian": "hy", "assamese": "as", "azerbaijani": "az", "basque": "eu",
    "belarusian": "be", "bengali": "bn", "bangla": "bn", "bosnian": "bs",
    "bulgarian": "bg", "burmese": "my", "catalan": "ca", "cebuano": "ceb",
    "chichewa": "ny", "chinese": "zh-CN", "chinese simplified": "zh-CN",
    "simplified chinese": "zh-CN", "chinese traditional": "zh-TW",
    "traditional chinese": "zh-TW", "corsican": "co", "croatian": "hr",
    "czech": "cs", "danish": "da", "dutch": "nl", "english": "en",
    "esperanto": "eo", "estonian": "et", "filipino": "tl", "finnish": "fi",
    "french": "fr", "frisian": "fy", "galician": "gl", "georgian": "ka",
    "german": "de", "greek": "el", "gujarati": "gu", "haitian creole": "ht",
    "hausa": "ha", "hawaiian": "haw", "hebrew": "he", "hindi": "hi",
    "hmong": "hmn", "hungarian": "hu", "icelandic": "is", "igbo": "ig",
    "indonesian": "id", "irish": "ga", "italian": "it", "japanese": "ja",
    "javanese": "jv", "kannada": "kn", "kazakh": "kk", "khmer": "km",
    "kinyarwanda": "rw", "korean": "ko", "kurdish": "ku", "kyrgyz": "ky",
    "lao": "lo", "latin": "la", "latvian": "lv", "lithuanian": "lt",
    "luxembourgish": "lb", "macedonian": "mk", "malagasy": "mg", "malay": "ms",
    "malayalam": "ml", "maltese": "mt", "maori": "mi", "marathi": "mr",
    "mongolian": "mn", "nepali": "ne", "norwegian": "no", "odia": "or",
    "oriya": "or", "pashto": "ps", "persian": "fa", "farsi": "fa",
    "polish": "pl", "portuguese": "pt", "brazilian portuguese": "pt-BR",
    "punjabi": "pa", "romanian": "ro", "russian": "ru", "samoan": "sm",
    "scots gaelic": "gd", "serbian": "sr", "sesotho": "st", "shona": "sn",
    "sindhi": "sd", "sinhala": "si", "slovak": "sk", "slovenian": "sl",
    "somali": "so", "spanish": "es", "sundanese": "su", "swahili": "sw",
    "swedish": "sv", "tajik": "tg", "tamil": "ta", "tatar": "tt",
    "telugu": "te", "thai": "th", "turkish": "tr", "turkmen": "tk",
    "ukrainian": "uk", "urdu": "ur", "uyghur": "ug", "uzbek": "uz",
    "vietnamese": "vi", "welsh": "cy", "xhosa": "xh", "yiddish": "yi",
    "yoruba": "yo", "zulu": "zu", "bhojpuri": "bho", "maithili": "mai",
}
_LANGUAGE_NAMES = {code.casefold(): name.title() for name, code in _LANGUAGE_ALIASES.items()
                   if name not in {"auto", "detect"}}
_LANGUAGE_NAMES.update({
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "pt-br": "Portuguese (Brazil)", "tl": "Filipino",
})


class TranslationUnavailable(RuntimeError):
    """No configured translation provider returned a usable translation."""


@dataclass(frozen=True)
class TranslationResult:
    text: str
    source_language: str
    target_language: str
    provider: str

    @property
    def source_name(self) -> str:
        return language_name(self.source_language)

    @property
    def target_name(self) -> str:
        return language_name(self.target_language)


def normalize_language_code(value: str, *, allow_auto: bool = False) -> str:
    """Resolve a language name or code into a service language code."""
    value = re.sub(r"\s+", " ", (value or "").strip())
    if not value:
        raise ValueError("Language is missing")
    alias = _LANGUAGE_ALIASES.get(value.casefold())
    if alias:
        if alias == "auto" and not allow_auto:
            raise ValueError("Choose a target language, not 'auto'")
        return alias
    # Accept common BCP-47/provider codes such as en, fr, zh-CN or pt-BR.
    if re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?", value):
        code_parts = value.split("-")
        return code_parts[0].lower() + ("-" + code_parts[1].upper() if len(code_parts) == 2 else "")
    raise ValueError(f"Unknown language '{value}'. Use a language name or code such as Spanish, Hindi, fr or ja.")


def language_name(code: str) -> str:
    if not code:
        return "Auto-detected"
    return _LANGUAGE_NAMES.get(code.casefold(), code.upper() if len(code) <= 3 else code)


def supported_language_examples() -> str:
    return (
        "Common targets: Arabic, Bengali, Chinese, Dutch, English, French, German, Greek, Gujarati, "
        "Hebrew, Hindi, Indonesian, Italian, Japanese, Kannada, Korean, Malayalam, Marathi, Nepali, "
        "Persian, Polish, Portuguese, Punjabi, Russian, Spanish, Tamil, Telugu, Thai, Turkish, Urdu, "
        "Vietnamese. You can also use provider codes for other languages."
    )


@dataclass(frozen=True)
class TranslationRequest:
    text: str
    target: str
    source: str = "auto"


def parse_translation_request(raw: str) -> TranslationRequest:
    """Parse a command body, e.g. ``Spanish | Hello`` or ``from Spanish to Hindi | Hi``.

    The pipe form supports language names containing spaces. Without a pipe,
    the first word is treated as the target language (``Spanish Hello there``).
    """
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Usage: /translate <target> | <text>")
    if "|" in raw:
        left, text = raw.split("|", 1)
        left, text = left.strip(), text.strip()
        explicit = re.fullmatch(r"from\s+(.+?)\s+to\s+(.+)", left, re.I)
        if explicit:
            source = normalize_language_code(explicit.group(1), allow_auto=True)
            target = normalize_language_code(explicit.group(2))
        else:
            source = "auto"
            target = normalize_language_code(left)
    else:
        parts = raw.split(None, 1)
        if len(parts) != 2:
            raise ValueError("Add text after the target. Example: /translate Spanish | Hello baby")
        source, target, text = "auto", normalize_language_code(parts[0]), parts[1].strip()
    if not text:
        raise ValueError("Text to translate is missing")
    return TranslationRequest(text=text, target=target, source=source)


class UniversalTranslator:
    """Keyless multilingual text translation with caching and provider fallback.

    A LibreTranslate-compatible URL is optional (AIKO_TRANSLATE_URL). Without
    it, the client uses Google's public translation web endpoint. The latter is
    unofficial and can be rate-limited, so this class never treats it as
    guaranteed availability. No text is saved to disk; only bounded in-memory
    cache entries are kept.
    """
    def __init__(self, endpoint: str | None = None, timeout: float = _TIMEOUT_SECONDS):
        self.endpoint = (endpoint if endpoint is not None else os.getenv("AIKO_TRANSLATE_URL", "")).strip().rstrip("/")
        self.timeout = max(1.0, min(float(timeout), 20.0))
        self._cache: OrderedDict[tuple[str, str, str], tuple[float, TranslationResult]] = OrderedDict()
        self._cache_lock = threading.RLock()
        self._request_lock = threading.Lock()
        self._last_request = 0.0

    def provider_status(self) -> str:
        providers = []
        if self.endpoint:
            providers.append("configured LibreTranslate-compatible endpoint")
        providers.append("Google Translate keyless web endpoint (unofficial fallback)")
        return "Translation providers: " + " → ".join(providers) + ". Translation only runs for /translate or /translate test; ordinary chat stays local."

    def _throttle(self) -> None:
        # Keep request volume polite; a cache hit never waits.
        with self._request_lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < 0.25:
                time.sleep(0.25 - elapsed)
            self._last_request = time.monotonic()

    def translate(self, text: str, target: str, source: str = "auto") -> TranslationResult:
        text = (text or "").strip()
        if not text:
            raise ValueError("Text to translate is empty")
        if len(text) > _MAX_CHARACTERS:
            raise ValueError(f"Text is too long ({len(text)} characters). Please keep each translation under {_MAX_CHARACTERS} characters.")
        target_code = normalize_language_code(target)
        source_code = normalize_language_code(source, allow_auto=True)
        if source_code != "auto" and source_code == target_code:
            return TranslationResult(text, source_code, target_code, "no translation needed")
        key = (source_code, target_code, text)
        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(key)
            if cached and now - cached[0] < _CACHE_TTL:
                self._cache.move_to_end(key)
                old = cached[1]
                return TranslationResult(old.text, old.source_language, old.target_language, old.provider + " (cached)")
            if cached:
                self._cache.pop(key, None)

        errors: list[Exception] = []
        providers = []
        if self.endpoint:
            providers.append(("LibreTranslate-compatible endpoint", self._translate_libre))
        providers.append(("Google Translate", self._translate_google))
        for provider_name, provider in providers:
            try:
                result_text, detected_source = provider(text, source_code, target_code)
                result_text = result_text.strip()
                if not result_text:
                    raise ValueError("empty translation result")
                result = TranslationResult(
                    text=result_text,
                    source_language=detected_source or source_code,
                    target_language=target_code,
                    provider=provider_name,
                )
                self._store_cache(key, result)
                return result
            except Exception as exc:
                errors.append(exc)
                # Logs identify only provider/error type. Never log user's text.
                _LOG.debug("Translation provider %s failed (%s)", provider_name, type(exc).__name__)
        raise TranslationUnavailable("Translation providers did not return a usable result") from (errors[-1] if errors else None)

    def _translate_libre(self, text: str, source: str, target: str) -> tuple[str, str]:
        if not self.endpoint:
            raise RuntimeError("No LibreTranslate endpoint configured")
        parsed = urlparse(self.endpoint)
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise ValueError("Translation endpoint must use HTTPS unless it is localhost")
        url = self.endpoint if self.endpoint.endswith("/translate") else self.endpoint + "/translate"
        payload = json.dumps({"q": text, "source": source, "target": target, "format": "text"}).encode("utf-8")
        request = Request(url, data=payload, headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": _USER_AGENT}, method="POST")
        self._throttle()
        with urlopen(request, timeout=self.timeout) as response:
            if getattr(response, "status", 200) >= 400:
                raise OSError(f"HTTP {response.status}")
            data = json.loads(response.read().decode("utf-8"))
        translated = data.get("translatedText") if isinstance(data, dict) else None
        detected = (data.get("detectedLanguage") or {}).get("language", "") if isinstance(data, dict) else ""
        if not isinstance(translated, str) or not translated.strip():
            raise ValueError("Malformed translation response")
        return translated, str(detected or source)

    def _translate_google(self, text: str, source: str, target: str) -> tuple[str, str]:
        params = urlencode({"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text})
        request = Request(
            "https://translate.googleapis.com/translate_a/single?" + params,
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            method="GET",
        )
        self._throttle()
        with urlopen(request, timeout=self.timeout) as response:
            if getattr(response, "status", 200) >= 400:
                raise OSError(f"HTTP {response.status}")
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, list) or not data or not isinstance(data[0], list):
            raise ValueError("Malformed translation response")
        translated_parts: list[str] = []
        for segment in data[0]:
            if isinstance(segment, list) and segment and isinstance(segment[0], str):
                translated_parts.append(segment[0])
        translated = "".join(translated_parts).strip()
        detected = data[2] if len(data) > 2 and isinstance(data[2], str) else source
        if not translated:
            raise ValueError("Empty translation response")
        return translated, detected

    def _store_cache(self, key: tuple[str, str, str], result: TranslationResult) -> None:
        with self._cache_lock:
            self._cache[key] = (time.monotonic(), result)
            self._cache.move_to_end(key)
            while len(self._cache) > _CACHE_SIZE:
                self._cache.popitem(last=False)

    def test(self) -> str:
        """Translate a fixed public sentence for a network diagnostic."""
        result = self.translate("Hello, how are you?", "Hindi")
        return f"Translation service reachable ✅ Provider: {result.provider}; result: {result.text!r}. This test used a fixed sentence, not your chat."


def translation_command(raw: str, translator: UniversalTranslator) -> str:
    """Run a /translate command body and return one chat-ready message."""
    command = (raw or "").strip()
    lowered = command.casefold()
    if lowered in {"", "help", "?"}:
        return (
            "Universal translator 🌍\n"
            "Only the text you explicitly submit is sent to a translation provider; regular chat stays local.\n"
            "/translate <target> | <text>\n"
            "/translate from <source> to <target> | <text>\n"
            "/translate languages — common language names/codes\n"
            "/translate status — configured provider order\n"
            "/translate test — fixed public test sentence\n\n"
            "Examples:\n"
            "/translate Spanish | I love you, baby\n"
            "/translate from Japanese to Hindi | こんにちは\n"
            "/translate fr | Bonjour, comment ça va?"
        )
    if lowered == "status":
        return translator.provider_status()
    if lowered == "languages":
        return supported_language_examples() + "\nUse /translate <language code> | <text> for less common languages."
    if lowered == "test":
        try:
            return translator.test()
        except (TranslationUnavailable, ValueError):
            return "Translation service abhi reachable nahi hai ji 😕 Normal chat still works; try again later or configure a trusted LibreTranslate-compatible endpoint."
    try:
        request = parse_translation_request(command)
        result = translator.translate(request.text, request.target, request.source)
    except ValueError as exc:
        return f"{exc}\nUse /translate help for examples."
    except TranslationUnavailable:
        return "Translation abhi complete nahi ho paayi ji 😕 Providers may be offline or rate-limiting requests. Try again later; your text isn't saved by this translator."
    source_label = result.source_name
    target_label = result.target_name
    return f"🌍 {source_label} → {target_label}\n\n{result.text}\n\nProvider: {result.provider}"
