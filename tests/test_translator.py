import json
from types import SimpleNamespace

import pytest

from aiko.translator import (
    TranslationUnavailable,
    UniversalTranslator,
    normalize_language_code,
    parse_translation_request,
    translation_command,
)


class FakeResponse:
    def __init__(self, value, status=200):
        self.value = value
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.value).encode("utf-8")


def google_payload(translated="Hola mundo", detected="en"):
    return [[[translated, "Hello world", None, None, 3]], None, detected]


def test_language_aliases_and_provider_codes():
    assert normalize_language_code("Spanish") == "es"
    assert normalize_language_code("Simplified Chinese") == "zh-CN"
    assert normalize_language_code("pt-BR") == "pt-BR"
    assert normalize_language_code("auto", allow_auto=True) == "auto"
    with pytest.raises(ValueError):
        normalize_language_code("definitely not a language")
    with pytest.raises(ValueError):
        normalize_language_code("auto")


def test_parse_pipe_form_with_target_language_name_containing_spaces():
    request = parse_translation_request("Simplified Chinese | Hello there")
    assert request.target == "zh-CN"
    assert request.source == "auto"
    assert request.text == "Hello there"


def test_parse_explicit_source_and_target():
    request = parse_translation_request("from Spanish to Hindi | Hola, ¿cómo estás?")
    assert request.source == "es"
    assert request.target == "hi"
    assert request.text == "Hola, ¿cómo estás?"


def test_parse_short_form_with_target_code():
    request = parse_translation_request("fr Bonjour tout le monde")
    assert request.target == "fr"
    assert request.text == "Bonjour tout le monde"


def test_google_endpoint_translates_without_api_key(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout, request.headers))
        return FakeResponse(google_payload("Hola, bebé", "en"))

    monkeypatch.setattr("aiko.translator.urlopen", fake_urlopen)
    translator = UniversalTranslator(timeout=4)
    result = translator.translate("Hello, baby", "Spanish")
    assert result.text == "Hola, bebé"
    assert result.source_language == "en"
    assert result.target_language == "es"
    assert result.provider == "Google Translate"
    assert len(calls) == 1
    assert "translate.googleapis.com/translate_a/single" in calls[0][0]
    assert "key=" not in calls[0][0].casefold()
    assert calls[0][1] == 4


def test_translation_cache_avoids_second_network_request(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(google_payload("Hola", "en"))

    monkeypatch.setattr("aiko.translator.urlopen", fake_urlopen)
    translator = UniversalTranslator()
    first = translator.translate("Hello", "Spanish")
    second = translator.translate("Hello", "Spanish")
    assert first.text == second.text == "Hola"
    assert len(calls) == 1
    assert "cached" in second.provider.casefold()


def test_configured_libretranslate_is_tried_before_google(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if request.full_url.startswith("https://translate.example/translate"):
            return FakeResponse({"translatedText": "Bonjour", "detectedLanguage": {"language": "en"}})
        return FakeResponse(google_payload())

    monkeypatch.setattr("aiko.translator.urlopen", fake_urlopen)
    translator = UniversalTranslator(endpoint="https://translate.example")
    result = translator.translate("Hello", "French")
    assert result.text == "Bonjour"
    assert result.provider == "LibreTranslate-compatible endpoint"
    assert calls == ["https://translate.example/translate"]


def test_libretranslate_failure_falls_back_to_google(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if request.full_url.startswith("https://translate.example"):
            raise OSError("403 forbidden")
        return FakeResponse(google_payload("Hola mundo", "en"))

    monkeypatch.setattr("aiko.translator.urlopen", fake_urlopen)
    translator = UniversalTranslator(endpoint="https://translate.example")
    result = translator.translate("Hello world", "Spanish")
    assert result.text == "Hola mundo"
    assert result.provider == "Google Translate"
    assert calls[0] == "https://translate.example/translate"
    assert "translate.googleapis.com/translate_a/single" in calls[1]


def test_non_https_remote_libre_endpoint_is_rejected_and_fallback_used(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(google_payload("Hola", "en"))

    monkeypatch.setattr("aiko.translator.urlopen", fake_urlopen)
    result = UniversalTranslator(endpoint="http://translate.example").translate("Hello", "Spanish")
    assert result.text == "Hola"
    assert calls[0].startswith("https://translate.googleapis.com/")


def test_translation_provider_failure_is_clean_and_not_echoing_private_prompt(monkeypatch):
    def fail(*_args, **_kwargs):
        raise OSError("provider unavailable")

    monkeypatch.setattr("aiko.translator.urlopen", fail)
    translator = UniversalTranslator()
    with pytest.raises(TranslationUnavailable):
        translator.translate("a very private phrase", "Hindi")
    answer = translation_command("Hindi | another private phrase", translator)
    assert "Translation abhi complete nahi" in answer
    assert "another private phrase" not in answer
    assert "403" not in answer


def test_translation_command_status_languages_and_test(monkeypatch):
    translator = UniversalTranslator()
    assert "Google Translate" in translation_command("status", translator)
    assert "Spanish" in translation_command("languages", translator)
    monkeypatch.setattr(translator, "translate", lambda text, target, source="auto": SimpleNamespace(
        text="आप कैसे हैं?", provider="Google Translate", target_language="hi", source_language="en",
        source_name="English", target_name="Hindi",
    ))
    assert "fixed sentence" in translation_command("test", translator)


def test_empty_or_too_long_inputs_are_rejected_without_network(monkeypatch):
    calls = []
    monkeypatch.setattr("aiko.translator.urlopen", lambda *a, **k: calls.append(a))
    translator = UniversalTranslator()
    with pytest.raises(ValueError, match="empty"):
        translator.translate("  ", "Hindi")
    with pytest.raises(ValueError, match="too long"):
        translator.translate("x" * 4501, "Hindi")
    assert calls == []


def test_explicit_same_source_target_is_noop(monkeypatch):
    monkeypatch.setattr("aiko.translator.urlopen", lambda *a, **k: pytest.fail("network must not run"))
    result = UniversalTranslator().translate("hello", "English", source="en")
    assert result.text == "hello"
    assert result.provider == "no translation needed"
