"""Salvataggio e caricamento della libreria su file JSON."""

import json
import os
from dataclasses import asdict

from core.models import Game, Playthrough
from core.paths import user_data_dir

DATA_DIR = user_data_dir()
LIBRARY_FILE = DATA_DIR / "game_library.json"
CORRUPTED_LIBRARY_FILE = DATA_DIR / "game_library_corrupted.json"
UPLOADED_LIBRARY_FILE = DATA_DIR / "game_library_uploaded.json"


def save_library(games: list[Game]) -> None:
    """Scrive l'intera libreria nel file JSON, sovrascrivendolo."""
    games_data = []
    for game in games:
        games_data.append(asdict(game))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LIBRARY_FILE, "w", encoding="utf-8") as file:
        json.dump(games_data, file, indent=4, ensure_ascii=False)


def game_from_dict(game_data: dict) -> Game:
    """Ricostruisce un gioco e le sue partite dai dati letti dal JSON."""
    playthroughs_data = game_data.pop("playthroughs", [])
    game = Game(**game_data)
    for playthrough_data in playthroughs_data:
        game.playthroughs.append(Playthrough(**playthrough_data))
    return game


def load_library() -> list[Game]:
    """Legge la libreria dal file JSON; se manca o è danneggiato restituisce una lista vuota."""
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as file:
            games_data = json.load(file)
        games = []
        for game_data in games_data:
            games.append(game_from_dict(game_data))
        return games
    except FileNotFoundError:
        print("Nessuna libreria trovata, ne inizia una nuova.")
        return []
    except (json.JSONDecodeError, TypeError):
        os.replace(LIBRARY_FILE, CORRUPTED_LIBRARY_FILE)
        print(f"Libreria danneggiata: salvata come '{CORRUPTED_LIBRARY_FILE}'. Iniziata una libreria vuota.")
        return []


def mark_library_uploaded() -> None:
    """Dopo il caricamento nell'account, rinomina il file locale: resta come copia, ma non viene più proposto."""
    if LIBRARY_FILE.exists():
        os.replace(LIBRARY_FILE, UPLOADED_LIBRARY_FILE)
