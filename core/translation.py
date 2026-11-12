"""Traduzione in italiano delle descrizioni dei giochi, con una cache su disco per non tradurre due volte."""

import json
from pathlib import Path
from typing import Protocol

import requests

from core.catalog import CatalogGame
from core.storage import DATA_DIR

TRANSLATIONS_FILE = DATA_DIR / "cache" / "translations.json"
DEEPL_FREE_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_PRO_URL = "https://api.deepl.com/v2/translate"
FREE_KEY_SUFFIX = ":fx"
TARGET_LANGUAGE = "IT"
TIMEOUT_SECONDS = 10


class TranslationError(Exception):
    """La traduzione non è riuscita: rete assente, chiave errata, quota finita."""


class Translator(Protocol):
    """Qualsiasi oggetto che sa tradurre un testo in italiano."""

    def translate(self, text: str) -> str:
        """Restituisce il testo tradotto in italiano."""
        ...


class NoTranslator:
    """Traduttore che lascia il testo com'è: si usa finché non c'è una chiave DeepL."""

    def translate(self, text: str) -> str:
        """Restituisce il testo originale."""
        return text


class DeepLTranslator:
    """Traduce con l'API di DeepL e salva ogni traduzione in un file, così la stessa descrizione costa una volta sola."""

    def __init__(self, api_key: str, cache_file: Path = TRANSLATIONS_FILE) -> None:
        self.api_key = api_key
        self.cache_file = cache_file

    def translate(self, text: str) -> str:
        """Restituisce la traduzione dalla cache se c'è, altrimenti la chiede a DeepL e la salva."""
        if text.strip() == "":
            return text
        cache = load_cache(self.cache_file)
        if text in cache:
            return cache[text]
        translation = self.request_translation(text)
        cache[text] = translation
        save_cache(self.cache_file, cache)
        return translation

    def request_translation(self, text: str) -> str:
        """Chiede la traduzione a DeepL."""
        try:
            response = requests.post(
                deepl_url(self.api_key),
                headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
                json={"text": [text], "target_lang": TARGET_LANGUAGE},
                timeout=TIMEOUT_SECONDS,
            )
        except requests.RequestException as error:
            raise TranslationError("Impossibile contattare DeepL.") from error
        if not response.ok:
            raise TranslationError(f"DeepL ha risposto con un errore ({response.status_code}).")
        return str(response.json()["translations"][0]["text"])


def deepl_url(api_key: str) -> str:
    """Restituisce l'indirizzo giusto: le chiavi del piano gratuito finiscono con ':fx' e usano un server diverso."""
    return DEEPL_FREE_URL if api_key.endswith(FREE_KEY_SUFFIX) else DEEPL_PRO_URL


def load_cache(cache_file: Path) -> dict[str, str]:
    """Restituisce le traduzioni già fatte; se il file manca o è danneggiato, un dizionario vuoto."""
    try:
        with open(cache_file, "r", encoding="utf-8") as file:
            cache: dict[str, str] = json.load(file)
        return cache
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache_file: Path, cache: dict[str, str]) -> None:
    """Scrive tutte le traduzioni nel file della cache."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=2)


def translate_summary(catalog_game: CatalogGame, translator: Translator) -> None:
    """Sostituisce la descrizione con quella tradotta; se la traduzione fallisce lascia l'originale."""
    try:
        catalog_game.summary = translator.translate(catalog_game.summary)
    except TranslationError:
        pass
