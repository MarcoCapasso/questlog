"""Regole e ricerche sulla libreria, senza interazione con l'utente."""

from datetime import date

from core.models import Game, Playthrough


PLAYTHROUGH_STATUSES = ["playing", "completed", "dropped"]
BACKLOG = "backlog"
SEARCH_STATUSES = [BACKLOG] + PLAYTHROUGH_STATUSES


def find_game_indices_by_title(games: list[Game], query: str) -> list[int]:
    """Restituisce gli indici dei giochi il cui titolo contiene il testo cercato."""
    matching_indices = []
    normalized_query = query.lower()

    for index, game in enumerate(games):
        if normalized_query in game.title.lower():
            matching_indices.append(index)
    return matching_indices


def find_game_indices_by_status(games: list[Game], status: str) -> list[int]:
    """Restituisce gli indici dei giochi con almeno una partita nello stato indicato; per il backlog, quelli senza partite."""
    matching_indices = []

    for index, game in enumerate(games):
        if status == BACKLOG:
            if is_backlog(game):
                matching_indices.append(index)
        elif has_playthrough_with_status(game, status):
            matching_indices.append(index)
    return matching_indices


def find_game_index_by_title(
    games: list[Game],
    title: str,
    ignore_index: int | None = None,
) -> int | None:
    """Restituisce l'indice del gioco con lo stesso titolo (maiuscole ignorate), escluso ignore_index."""
    for index, game in enumerate(games):
        if index == ignore_index:
            continue
        if game.title.lower() == title.lower():
            return index
    return None


def is_backlog(game: Game) -> bool:
    """Indica se il gioco non è mai stato iniziato, cioè non ha partite."""
    return len(game.playthroughs) == 0


def has_playthrough_with_status(game: Game, status: str) -> bool:
    """Indica se almeno una partita del gioco ha lo stato indicato."""
    for playthrough in game.playthroughs:
        if playthrough.status == status:
            return True
    return False


def has_completed_playthrough(game: Game) -> bool:
    """Indica se il gioco è stato completato almeno una volta."""
    return has_playthrough_with_status(game, "completed")


def calculate_total_hours(game: Game) -> float:
    """Restituisce la somma delle ore di tutte le partite del gioco."""
    total_hours = 0.0
    for playthrough in game.playthroughs:
        total_hours += playthrough.hours_played
    return total_hours


def remove_playthrough(game: Game, playthrough_index: int) -> None:
    """Elimina una partita; se era l'ultima, il gioco torna in backlog e perde il voto."""
    game.playthroughs.pop(playthrough_index)
    if is_backlog(game):
        game.rating = None


def today_iso() -> str:
    """Restituisce la data di oggi in formato ISO (AAAA-MM-GG)."""
    today = date.today()
    return today.isoformat()


def apply_status_change(playthrough: Playthrough, new_status: str, today: str) -> None:
    """Cambia lo stato di una partita e aggiorna le sue date secondo le regole."""
    playthrough.status = new_status
    if playthrough.start_date is None:
        playthrough.start_date = today
    if new_status == "completed":
        if playthrough.completion_date is None:
            playthrough.completion_date = today
    else:
        playthrough.completion_date = None


def is_valid_rating(rating: float) -> bool:
    """Indica se il voto è tra 1 e 10, intero o a mezzi punti."""
    return 1 <= rating <= 10 and (rating * 2).is_integer()


def is_valid_date_order(start_date: str | None, completion_date: str | None) -> bool:
    """Indica se il completamento non precede l'inizio; sempre vero se manca una delle due date."""
    if start_date is None or completion_date is None:
        return True
    return completion_date >= start_date


def find_platform_spelling(games: list[Game], platform: str) -> str:
    """Restituisce la grafia già usata in libreria per la piattaforma (maiuscole ignorate), altrimenti quella inserita."""
    for game in games:
        for playthrough in game.playthroughs:
            if playthrough.platform.lower() == platform.lower():
                return playthrough.platform
    return platform


def summary_status(game: Game) -> str:
    """Restituisce lo stato che riassume il gioco: in corso, completato, abbandonato o backlog."""
    if is_backlog(game):
        return BACKLOG
    for status in PLAYTHROUGH_STATUSES:
        if has_playthrough_with_status(game, status):
            return status
    return BACKLOG


def filter_games(games: list[Game], query: str = "", status: str | None = None) -> list[Game]:
    """Restituisce i giochi il cui titolo contiene il testo cercato e, se indicato, con quello stato riassuntivo."""
    normalized_query = query.strip().lower()
    matching_games = []
    for game in games:
        if normalized_query not in game.title.lower():
            continue
        if status is not None and summary_status(game) != status:
            continue
        matching_games.append(game)
    return matching_games


def count_by_summary_status(games: list[Game]) -> dict[str, int]:
    """Restituisce quanti giochi ci sono per ogni stato riassuntivo, compresi quelli a zero."""
    counts = {status: 0 for status in PLAYTHROUGH_STATUSES + [BACKLOG]}
    for game in games:
        counts[summary_status(game)] += 1
    return counts


def playthrough_statuses(game: Game) -> list[str]:
    """Restituisce gli stati diversi delle partite del gioco, nell'ordine di priorità di PLAYTHROUGH_STATUSES."""
    statuses = []
    for status in PLAYTHROUGH_STATUSES:
        if has_playthrough_with_status(game, status):
            statuses.append(status)
    return statuses


def validate_new_title(games: list[Game], title: str) -> str | None:
    """Restituisce il messaggio d'errore per il titolo di un nuovo gioco, oppure None se è valido."""
    clean_title = title.strip()
    if clean_title == "":
        return "Il titolo non può essere vuoto."
    if find_game_index_by_title(games, clean_title) is not None:
        return f"'{clean_title}' è già nella libreria."
    return None