"""Salvataggio e caricamento della libreria su file JSON."""

import json
import os


LIBRARY_FILE = "game_library.json"
CORRUPTED_LIBRARY_FILE = "game_library_corrupted.json"


def save_library(games: list[dict]) -> None:
    """Scrive l'intera libreria nel file JSON, sovrascrivendolo."""
    with open(LIBRARY_FILE, "w", encoding="utf-8") as file:
        json.dump(games, file, indent=4, ensure_ascii=False)


def load_library() -> list[dict]:
    """Legge la libreria dal file JSON; se manca o è danneggiato restituisce una lista vuota."""
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as file:
            games = json.load(file)
            return games
    except FileNotFoundError:
        print("Nessuna libreria trovata, ne inizia una nuova.")
        return []
    except json.JSONDecodeError:
        os.replace(LIBRARY_FILE, CORRUPTED_LIBRARY_FILE)
        print(f"Libreria danneggiata: salvata come '{CORRUPTED_LIBRARY_FILE}'. Iniziata una libreria vuota.")
        return []