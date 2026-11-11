"""Impostazioni lette dal file .env, che resta sul tuo PC e non finisce mai su GitHub."""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(".env")


def load_igdb_credentials() -> tuple[str, str] | None:
    """Restituisce Client ID e Client Secret di IGDB, oppure None se non sono configurati."""
    load_dotenv(ENV_FILE)
    client_id = os.getenv("IGDB_CLIENT_ID", "").strip()
    client_secret = os.getenv("IGDB_CLIENT_SECRET", "").strip()
    if client_id == "" or client_secret == "":
        return None
    return client_id, client_secret
