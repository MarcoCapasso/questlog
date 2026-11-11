"""Catalogo IGDB: ricerca e sezioni (tendenze, nuove uscite, in arrivo) tramite l'API di IGDB."""

import time
from typing import Any

import requests

from core.catalog import CatalogGame

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
API_URL = "https://api.igdb.com/v4"
COVER_URL = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"
GAME_FIELDS = "fields name, cover.image_id, first_release_date, platforms.name, genres.name, summary;"
TIMEOUT_SECONDS = 10
SECTION_SIZE = 20
SEARCH_SIZE = 30
NEW_RELEASES_DAYS = 60
SECONDS_PER_DAY = 24 * 60 * 60
TRENDING_POPULARITY_TYPE = 1
TOKEN_SAFETY_SECONDS = 60


class IgdbError(Exception):
    """IGDB non ha risposto come previsto: rete assente, credenziali errate, richiesta non valida."""


class IgdbCatalog:
    """Catalogo che legge i dati da IGDB, autenticandosi con le credenziali dell'app Twitch."""

    is_demo = False

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: str | None = None
        self.token_expires_at = 0.0

    def search(self, text: str) -> list[CatalogGame]:
        """Restituisce i giochi trovati da IGDB per il testo cercato, in ordine di pertinenza."""
        return parse_games(self.query("games", build_search_query(text)))

    def trending(self) -> list[CatalogGame]:
        """Restituisce i giochi più visitati su IGDB in questo periodo."""
        popularity = self.query(
            "popularity_primitives",
            f"fields game_id, value; where popularity_type = {TRENDING_POPULARITY_TYPE}; "
            f"sort value desc; limit {SECTION_SIZE};",
        )
        game_ids = [row["game_id"] for row in popularity]
        if not game_ids:
            return []
        ids_text = ", ".join(str(game_id) for game_id in game_ids)
        games = parse_games(self.query("games", f"{GAME_FIELDS} where id = ({ids_text}); limit {SECTION_SIZE};"))
        return sorted(games, key=lambda game: game_ids.index(game.igdb_id))

    def new_releases(self) -> list[CatalogGame]:
        """Restituisce i giochi attesi usciti negli ultimi giorni, dal più recente."""
        now = int(time.time())
        since = now - NEW_RELEASES_DAYS * SECONDS_PER_DAY
        return parse_games(self.query(
            "games",
            f"{GAME_FIELDS} where first_release_date >= {since} & first_release_date <= {now} "
            f"& hypes > 0 & cover != null & version_parent = null; "
            f"sort first_release_date desc; limit {SECTION_SIZE};",
        ))

    def upcoming(self) -> list[CatalogGame]:
        """Restituisce i giochi non ancora usciti, dal più atteso."""
        now = int(time.time())
        return parse_games(self.query(
            "games",
            f"{GAME_FIELDS} where first_release_date > {now} & hypes > 0 "
            f"& cover != null & version_parent = null; sort hypes desc; limit {SECTION_SIZE};",
        ))

    def details(self, igdb_id: int) -> CatalogGame | None:
        """Restituisce il gioco con quell'id IGDB, oppure None se non esiste."""
        games = parse_games(self.query("games", f"{GAME_FIELDS} where id = {igdb_id};"))
        return games[0] if games else None

    def query(self, endpoint: str, body: str) -> list[dict[str, Any]]:
        """Invia una richiesta all'API di IGDB e restituisce le righe della risposta."""
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.token()}"}
        try:
            response = requests.post(f"{API_URL}/{endpoint}", data=body, headers=headers, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as error:
            raise IgdbError("Impossibile contattare IGDB: controlla la connessione.") from error
        if response.status_code == 401:
            self.access_token = None
            raise IgdbError("IGDB ha rifiutato l'accesso: controlla le credenziali.")
        if not response.ok:
            raise IgdbError(f"IGDB ha risposto con un errore ({response.status_code}).")
        rows: list[dict[str, Any]] = response.json()
        return rows

    def token(self) -> str:
        """Restituisce un token di accesso valido, chiedendone uno nuovo a Twitch se manca o sta per scadere."""
        if self.access_token is not None and time.time() < self.token_expires_at:
            return self.access_token
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        try:
            response = requests.post(TOKEN_URL, params=params, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as error:
            raise IgdbError("Impossibile contattare Twitch: controlla la connessione.") from error
        if not response.ok:
            raise IgdbError("Twitch ha rifiutato le credenziali: controlla Client ID e Client Secret.")
        data = response.json()
        self.access_token = str(data["access_token"])
        self.token_expires_at = time.time() + data["expires_in"] - TOKEN_SAFETY_SECONDS
        return self.access_token


def build_search_query(text: str) -> str:
    """Restituisce la richiesta IGDB per cercare un titolo; le virgolette sono tolte per non rompere la sintassi."""
    clean_text = text.replace('"', "").strip()
    return f'search "{clean_text}"; {GAME_FIELDS} where version_parent = null; limit {SEARCH_SIZE};'


def parse_games(rows: list[dict[str, Any]]) -> list[CatalogGame]:
    """Trasforma le righe JSON di IGDB in giochi del catalogo."""
    return [parse_game(row) for row in rows]


def parse_game(row: dict[str, Any]) -> CatalogGame:
    """Trasforma una riga JSON di IGDB in un gioco del catalogo; i campi mancanti restano vuoti."""
    cover = row.get("cover")
    cover_url = COVER_URL.format(image_id=cover["image_id"]) if cover else None
    release_timestamp = row.get("first_release_date")
    release_year = time.gmtime(release_timestamp).tm_year if release_timestamp is not None else None
    return CatalogGame(
        igdb_id=row["id"],
        title=row["name"],
        cover_url=cover_url,
        release_year=release_year,
        platforms=[platform["name"] for platform in row.get("platforms", [])],
        genres=[genre["name"] for genre in row.get("genres", [])],
        summary=row.get("summary", ""),
    )
