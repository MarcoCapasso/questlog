"""La libreria salvata su Supabase: lettura e scrittura via rete, da chiamare in background.

Le regole RLS fanno vedere a ogni utente solo le sue righe: qui non serve mai filtrare per utente.
"""

from collections.abc import Callable
from typing import Any, cast

from httpx import HTTPError
from postgrest.exceptions import APIError
from supabase import Client

from core.cloud import CloudError
from core.models import Game, Playthrough

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
