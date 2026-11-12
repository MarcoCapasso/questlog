import requests

from core.catalog import CatalogGame
from core.translation import (
    DEEPL_FREE_URL,
    DEEPL_PRO_URL,
    DeepLTranslator,
    TranslationError,
    deepl_url,
    translate_summary,
)


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        self.ok = status_code < 400

    def json(self):
        return self.data


class FailingTranslator:
    def translate(self, text):
        raise TranslationError("niente rete")


def test_free_keys_use_the_free_server():
    assert deepl_url("abc:fx") == DEEPL_FREE_URL
    assert deepl_url("abc") == DEEPL_PRO_URL


def test_translation_is_cached_and_requested_once(tmp_path, monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"]["text"])
        return FakeResponse({"translations": [{"text": "Ciao mondo"}]})

    monkeypatch.setattr(requests, "post", fake_post)
    translator = DeepLTranslator("chiave:fx", tmp_path / "translations.json")

    assert translator.translate("Hello world") == "Ciao mondo"
    assert translator.translate("Hello world") == "Ciao mondo"
    assert len(calls) == 1


def test_failed_translation_keeps_original_summary():
    game = CatalogGame(1, "Celeste", summary="Climb the mountain.")

    translate_summary(game, FailingTranslator())

    assert game.summary == "Climb the mountain."
