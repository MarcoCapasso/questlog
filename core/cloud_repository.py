"""La libreria salvata su Supabase: lettura e scrittura via rete, da chiamare in background.

Le regole RLS fanno vedere a ogni utente solo le sue righe: qui non serve mai filtrare per utente.
"""

from collections.abc import Callable
from datetime import date
from typing import Any, cast

from httpx import HTTPError
from postgrest.exceptions import APIError
from supabase import Client

from core.cloud import CloudError
from core.library import MAX_RATING
from core.models import Game, Playthrough

VALID_STATUSES = ("playing", "completed", "dropped")
MAX_HOURS = 999_999.9
GAME_COLUMNS = (
    "title, rating, igdb_id, cover_url, position, "
    "playthroughs(platform, status, hours_played, start_date, completion_date, notes, position)"
)


class SupabaseGameRepository:
    """Legge e salva la libreria dell'utente che ha fatto login, nelle tabelle games e playthroughs."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def fetch_games(self) -> list[Game]:
        """Scarica tutti i giochi dell'utente con le loro partite, nell'ordine in cui erano salvati."""
        response = call_database(
            "leggere la libreria", lambda: self.client.table("games").select(GAME_COLUMNS).execute()
        )
        rows = sorted(cast(list[dict[str, Any]], response.data), key=lambda row: row["position"])
        return [game_from_row(row) for row in rows]

    def upload_games(self, games: list[Game]) -> None:
        """Sostituisce la libreria online con questa, tutta insieme (vedi replace_library in schema.sql)."""
        library = [game_to_row(game) for game in games]
        call_database(
            "salvare la libreria", lambda: self.client.rpc("replace_library", {"library": library}).execute()
        )


def call_database[T](action: str, request: Callable[[], T]) -> T:
    """Esegue una richiesta al database; se fallisce, la trasforma in un CloudError in italiano."""
    try:
        return request()
    except APIError as error:
        raise CloudError(f"Non riesco a {action} online: {error.message}") from error
    except HTTPError as error:
        raise CloudError(f"Non riesco a {action} online: controlla la connessione.") from error


def game_to_row(game: Game) -> dict[str, Any]:
    """Trasforma un gioco nel JSON che si aspetta replace_library."""
    return {
        "title": game.title,
        "rating": round(game.rating) if game.rating is not None else None,
        "igdb_id": game.igdb_id,
        "cover_url": game.cover_url,
        "playthroughs": [
            {
                "platform": playthrough.platform,
                "status": playthrough.status,
                "hours_played": playthrough.hours_played,
                "start_date": playthrough.start_date,
                "completion_date": playthrough.completion_date,
                "notes": playthrough.notes,
            }
            for playthrough in game.playthroughs
        ],
    }


def game_from_row(row: dict[str, Any]) -> Game:
    """Trasforma una riga di games (con le sue playthroughs annidate) in un Game."""
    playthrough_rows = sorted(row.get("playthroughs") or [], key=lambda item: item["position"])
    return Game(
        title=row["title"],
        rating=row["rating"],
        playthroughs=[
            Playthrough(
                platform=item["platform"],
                status=item["status"],
                hours_played=float(item["hours_played"]),
                start_date=item["start_date"],
                completion_date=item["completion_date"],
                notes=item["notes"],
            )
            for item in playthrough_rows
        ],
        igdb_id=row["igdb_id"],
        cover_url=row["cover_url"],
    )


def split_valid_games(games: list[Game]) -> tuple[list[Game], list[str]]:
    """Divide i giochi tra quelli che il database accetta e i problemi di quelli che rifiuterebbe.

    Sono le stesse regole dei check di schema.sql, controllate prima dell'invio: così un solo gioco
    sbagliato non fa fallire il caricamento di tutta la libreria. Restituisce (giochi validi, problemi).
    """
    valid: list[Game] = []
    problems: list[str] = []
    seen_titles: set[str] = set()
    seen_igdb_ids: set[int] = set()
    for game in games:
        problem = find_game_problem(game)
        if problem is None and game.title.strip().lower() in seen_titles:
            problem = "c'è già un gioco con questo titolo"
        if problem is None and game.igdb_id is not None and game.igdb_id in seen_igdb_ids:
            problem = "è già collegato a un altro gioco della libreria"
        if problem is not None:
            problems.append(f"{game.title or 'Gioco senza titolo'}: {problem}")
            continue
        seen_titles.add(game.title.strip().lower())
        if game.igdb_id is not None:
            seen_igdb_ids.add(game.igdb_id)
        valid.append(game)
    return valid, problems


def find_game_problem(game: Game) -> str | None:
    """Restituisce il primo motivo per cui il database rifiuterebbe questo gioco, oppure None."""
    if game.title.strip() == "":
        return "manca il titolo"
    if game.rating is not None and not 1 <= game.rating <= MAX_RATING:
        return f"il voto deve essere da 1 a {MAX_RATING} stelle"
    for playthrough in game.playthroughs:
        problem = find_playthrough_problem(playthrough)
        if problem is not None:
            return problem
    return None


def find_playthrough_problem(playthrough: Playthrough) -> str | None:
    """Restituisce il primo motivo per cui il database rifiuterebbe questa partita, oppure None."""
    if playthrough.platform.strip() == "":
        return "una partita non ha la piattaforma"
    if playthrough.status not in VALID_STATUSES:
        return f"stato sconosciuto ({playthrough.status})"
    if not 0 <= playthrough.hours_played <= MAX_HOURS:
        return "ore di gioco non valide"
    if playthrough.status == "completed" and playthrough.hours_played == 0:
        return "una partita completata ha 0 ore"
    if playthrough.status != "completed" and playthrough.completion_date is not None:
        return "una partita non completata ha la data di fine"
    try:
        start = date.fromisoformat(playthrough.start_date) if playthrough.start_date else None
        end = date.fromisoformat(playthrough.completion_date) if playthrough.completion_date else None
    except ValueError:
        return "una data non è valida"
    if start is not None and end is not None and end < start:
        return "una partita finisce prima di iniziare"
    return None
