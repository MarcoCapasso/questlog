"""Impostazioni lette dal file .env, che resta sul tuo PC e non finisce mai su GitHub."""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(".env")


def read_setting(name: str) -> str | None:
    """Restituisce il valore di un'impostazione del file .env, oppure None se manca o è vuota."""
    load_dotenv(ENV_FILE)
    value = os.getenv(name, "").strip()
    return value if value != "" else None


def load_supabase_settings() -> tuple[str, str] | None:
    """Restituisce URL del progetto e chiave pubblica di Supabase, oppure None se non sono configurati."""
    url = read_setting("SUPABASE_URL")
    key = read_setting("SUPABASE_ANON_KEY")
    if url is None or key is None:
        return None
    base_url = url.rstrip("/").removesuffix("/rest/v1")
    return base_url, key


def load_deepl_api_key() -> str | None:
    """Restituisce la chiave di DeepL per tradurre le descrizioni, oppure None se non è configurata."""
    return read_setting("DEEPL_API_KEY")
