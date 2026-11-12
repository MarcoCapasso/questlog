"""Impostazioni dell'app: dal file .env (sviluppo) oppure da quelle incluse nell'.exe al momento del build.

Il file .env resta sul tuo PC e non finisce mai su GitHub né dentro l'.exe.
Nell'.exe ci sono solo le impostazioni PUBBLICHE (PUBLIC_SETTINGS), copiate dal .env dallo script di build.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from core.paths import resource_dir

ENV_FILE = Path(".env")
BUNDLED_SETTINGS_FILE = resource_dir() / "app_settings.json"
# Le sole impostazioni che possono finire nell'.exe: sono pubbliche per definizione.
PUBLIC_SETTINGS = ("SUPABASE_URL", "SUPABASE_ANON_KEY")


def read_setting(name: str) -> str | None:
    """Restituisce un'impostazione: prima dal file .env, poi da quelle incluse nell'.exe; None se manca."""
    load_dotenv(ENV_FILE)
    value = os.getenv(name, "").strip()
    if value != "":
        return value
    return read_bundled_setting(name)


def read_bundled_setting(name: str) -> str | None:
    """Restituisce un'impostazione dal file incluso nell'.exe, oppure None se il file o il valore mancano."""
    try:
        settings = json.loads(BUNDLED_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    value = str(settings.get(name, "")).strip()
    return value if value != "" else None


def write_bundled_settings(path: Path) -> list[str]:
    """Scrive in path le impostazioni pubbliche lette dal .env; restituisce quelle che mancano.

    La usa lo script di build: qualsiasi altra chiave del .env (per esempio DEEPL_API_KEY) resta fuori.
    """
    load_dotenv(ENV_FILE)
    settings = {name: os.getenv(name, "").strip() for name in PUBLIC_SETTINGS}
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return [name for name, value in settings.items() if value == ""]


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
