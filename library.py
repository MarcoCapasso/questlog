"""Regole e ricerche sulla libreria, senza interazione con l'utente."""

from datetime import date

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


def today_iso() -> str:
    """Restituisce la data di oggi in formato ISO (AAAA-MM-GG)."""
    today = date.today()
    return today.isoformat()


def apply_status_change(game: Game, new_status: str, today: str) -> None:
    """Cambia lo stato di un gioco e aggiorna date e voto secondo le regole."""
    game.status = new_status
    if new_status == "backlog":
        game.start_date = None
        game.completion_date = None
        game.rating = None
    elif new_status == "completed":
        if game.start_date is None:
            game.start_date = today
        if game.completion_date is None:
            game.completion_date = today
    else:
        if game.start_date is None:
            game.start_date = today
        game.completion_date = None


def is_valid_date_order(start_date: str | None, completion_date: str | None) -> bool:
    """Indica se il completamento non precede l'inizio; sempre vero se manca una delle due date."""
    if start_date is None or completion_date is None:
        return True
    return completion_date >= start_date