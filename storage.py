"""Salvataggio e caricamento della libreria su file JSON."""

import json
import os
from dataclasses import asdict

from models import Game


LIBRARY_FILE = "game_library.json"
CORRUPTED_LIBRARY_FILE = "game_library_corrupted.json"


def save_library(games: list[Game]) -> None:
    """Scrive l'intera libreria nel file JSON, sovrascrivendolo."""
    games_data = []
    for game in games:
        games_data.append(asdict(game))
    with open(LIBRARY_FILE, "w", encoding="utf-8") as file:
        json.dump(games_data, file, indent=4, ensure_ascii=False)


def load_library() -> list[Game]:
    """Legge la libreria dal file JSON; se manca o è danneggiato restituisce una lista vuota."""
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as file:
            games_data = json.load(file)
        games = []
        for game_data in games_data:
            games.append(Game(**game_data))
        return games
    except FileNotFoundError:
        print("Nessuna libreria trovata, ne inizia una nuova.")
        return []
    except (json.JSONDecodeError, TypeError):
        os.replace(LIBRARY_FILE, CORRUPTED_LIBRARY_FILE)
        print(f"Libreria danneggiata: salvata come '{CORRUPTED_LIBRARY_FILE}'. Iniziata una libreria vuota.")
        return []