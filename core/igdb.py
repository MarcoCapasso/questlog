"""Catalogo IGDB: ricerca, sezioni e dettagli tramite la Edge Function "igdb" di Supabase.

L'app non parla più direttamente con IGDB: chiede alla funzione sul server, che ha le credenziali
e accetta solo le richieste del catalogo (vedi supabase/functions/igdb). Qui si trasformano
le righe di IGDB in CatalogGame.
"""

import time
from typing import Any, cast

from httpx import HTTPError
from supabase import Client
from supabase_functions.errors import FunctionsError

from core.catalog import CatalogGame
from core.platforms import normalize_platforms

FUNCTION_NAME = "igdb"
IMAGE_URL = "https://images.igdb.com/igdb/image/upload/{size}/{image_id}.jpg"
COVER_SIZE = "t_cover_big"
SCREENSHOT_SIZE = "t_screenshot_big"
BACKDROP_SIZE = "t_1080p"
UNAUTHORIZED = 401


class IgdbError(Exception):
    """Il catalogo non ha risposto come previsto: rete assente, login scaduto, errore di IGDB."""


class IgdbCatalog:
    """Catalogo che legge i dati di IGDB passando dalla Edge Function, con il login dell'utente."""

    is_demo = False

    def __init__(self, client: Client) -> None:
        self.client = client

    def search(self, text: str) -> list[CatalogGame]:
        """Restituisce i giochi trovati per il testo cercato, in ordine di pertinenza."""
        return parse_games(self.call({"action": "search", "text": text}))

    def trending(self) -> list[CatalogGame]:
        """Restituisce i giochi più visitati su IGDB in questo periodo."""
        return parse_games(self.call({"action": "trending"}))

    def new_releases(self) -> list[CatalogGame]:
        """Restituisce i giochi attesi usciti negli ultimi giorni, dal più recente."""
        return parse_games(self.call({"action": "new_releases"}))

    def upcoming(self) -> list[CatalogGame]:
        """Restituisce i giochi non ancora usciti, dal più atteso."""
        return parse_games(self.call({"action": "upcoming"}))

    def details(self, igdb_id: int) -> CatalogGame | None:
        """Restituisce il gioco con quell'id IGDB, oppure None se non esiste."""
        games = parse_games(self.call({"action": "details", "id": igdb_id}))
        return games[0] if games else None

    def call(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        """Manda un'azione alla Edge Function e restituisce le righe di IGDB della risposta.

        Il client Supabase aggiunge da solo il token dell'utente loggato: senza login la funzione risponde 401.
        """
        try:
            response = self.client.functions.invoke(
                FUNCTION_NAME, invoke_options={"body": request, "responseType": "json"}
            )
        except FunctionsError as error:
            if error.status == UNAUTHORIZED:
                raise IgdbError("Per usare il catalogo serve il login.") from error
            raise IgdbError(error.message) from error
        except HTTPError as error:
            raise IgdbError("Impossibile contattare il catalogo: controlla la connessione.") from error
        data = cast(dict[str, Any], response)
        return cast(list[dict[str, Any]], data["games"])


def parse_games(rows: list[dict[str, Any]]) -> list[CatalogGame]:
    """Trasforma le righe JSON di IGDB in giochi del catalogo."""
    return [parse_game(row) for row in rows]


def parse_game(row: dict[str, Any]) -> CatalogGame:
    """Trasforma una riga JSON di IGDB in un gioco del catalogo; i campi mancanti restano vuoti."""
    cover = row.get("cover")
    cover_url = image_url(cover["image_id"], COVER_SIZE) if cover else None
    screenshot_ids = [image["image_id"] for image in row.get("screenshots", [])]
    artwork_ids = [image["image_id"] for image in row.get("artworks", [])]
    backdrop_ids = artwork_ids + screenshot_ids
    release_timestamp = row.get("first_release_date")
    release_year = time.gmtime(release_timestamp).tm_year if release_timestamp is not None else None
    return CatalogGame(
        igdb_id=row["id"],
        title=row["name"],
        cover_url=cover_url,
        release_year=release_year,
        platforms=normalize_platforms([platform["name"] for platform in row.get("platforms", [])]),
        genres=[genre["name"] for genre in row.get("genres", [])],
        summary=row.get("summary", ""),
        screenshot_urls=[image_url(image_id, SCREENSHOT_SIZE) for image_id in screenshot_ids],
        backdrop_url=image_url(backdrop_ids[0], BACKDROP_SIZE) if backdrop_ids else None,
    )


def image_url(image_id: str, size: str) -> str:
    """Restituisce l'indirizzo di un'immagine IGDB nella dimensione indicata (copertina, screenshot, 1080p)."""
    return IMAGE_URL.format(size=size, image_id=image_id)
