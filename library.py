"""Regole e ricerche sulla libreria, senza interazione con l'utente."""

from models import Game

ALLOWED_STATUSES = ["backlog", "playing", "completed", "dropped"]


def find_game_indices_by_title(games: list[Game], query: str) -> list[int]:
    """Restituisce gli indici dei giochi il cui titolo contiene il testo cercato."""
    matching_indices = []
    normalized_query = query.lower()

    for index, game in enumerate(games):
        if normalized_query in game.title.lower():
            matching_indices.append(index)
    return matching_indices


def find_game_indices_by_status(games: list[Game], status: str) -> list[int]:
    """Restituisce gli indici dei giochi con lo stato indicato."""
    matching_indices = []

    for index, game in enumerate(games):
        if status == game.status:
            matching_indices.append(index)
    return matching_indices


def is_duplicate_game(
    games: list[Game],
    title: str,
    platform: str,
    ignore_index: int | None = None,
) -> bool:
    """Indica se esiste già un gioco con stesso titolo e piattaforma, escluso ignore_index."""
    for index, game in enumerate(games):
        if index == ignore_index:
            continue
        same_title = game.title.lower() == title.lower()
        same_platform = game.platform.lower() == platform.lower()
        if same_title and same_platform:
            return True
    return False