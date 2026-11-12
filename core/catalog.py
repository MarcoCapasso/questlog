"""Catalogo dei giochi esistenti (IGDB o uno finto), indipendente da dove arrivano i dati."""

from dataclasses import dataclass, field
from typing import Protocol

from core.library import find_game_index_by_title
from core.models import Game


@dataclass
class CatalogGame:
    """Un gioco del catalogo: non è ancora nella libreria, descrive solo il gioco."""
    igdb_id: int
    title: str
    cover_url: str | None = None
    release_year: int | None = None
    platforms: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    summary: str = ""
    screenshot_urls: list[str] = field(default_factory=list)
    backdrop_url: str | None = None


class GameCatalog(Protocol):
    """Qualsiasi oggetto che sa cercare giochi e proporre le sezioni del catalogo."""

    is_demo: bool

    def search(self, text: str) -> list[CatalogGame]:
        """Restituisce i giochi il cui titolo corrisponde al testo cercato."""
        ...

    def trending(self) -> list[CatalogGame]:
        """Restituisce i giochi più visti in questo periodo."""
        ...

    def new_releases(self) -> list[CatalogGame]:
        """Restituisce i giochi usciti di recente."""
        ...

    def upcoming(self) -> list[CatalogGame]:
        """Restituisce i giochi in uscita più attesi."""
        ...

    def details(self, igdb_id: int) -> CatalogGame | None:
        """Restituisce il gioco con quell'id IGDB, oppure None se non esiste."""
        ...


DEMO_GAMES = [
    CatalogGame(1, "Hollow Knight", None, 2017, ["PC", "Nintendo Switch", "PS4"], ["Platform", "Adventure"],
                "Scendi nelle rovine di Nidosacro, un regno di insetti caduto in rovina."),
    CatalogGame(2, "Outer Wilds", None, 2019, ["PC", "PS4", "Nintendo Switch"], ["Adventure", "Puzzle"],
                "Esplora un sistema solare intrappolato in un ciclo di ventidue minuti."),
    CatalogGame(3, "Elden Ring", None, 2022, ["PC", "PS5", "Xbox Series X|S"], ["Role-playing (RPG)"],
                "Un open world dark fantasy firmato FromSoftware."),
    CatalogGame(4, "Dredge", None, 2023, ["PC", "Nintendo Switch", "PS5"], ["Adventure", "Simulator"],
                "Un gioco di pesca con qualcosa di inquietante sotto la superficie."),
    CatalogGame(5, "Balatro", None, 2024, ["PC", "Nintendo Switch", "PS5"], ["Card & Board Game"],
                "Un roguelike di poker in cui costruisci mani sempre più assurde."),
    CatalogGame(6, "Celeste", None, 2018, ["PC", "Nintendo Switch"], ["Platform"],
                "Aiuta Madeline a scalare la montagna Celeste."),
    CatalogGame(7, "Hades II", None, 2025, ["PC", "Nintendo Switch 2"], ["Role-playing (RPG)", "Hack and slash"],
                "Melinoë combatte oltre gli Inferi contro il Titano del Tempo."),
    CatalogGame(8, "Hollow Knight: Silksong", None, 2025, ["PC", "Nintendo Switch 2", "PS5"], ["Platform"],
                "Hornet esplora un nuovo regno pieno di seta e canzoni."),
    CatalogGame(9, "Disco Elysium", None, 2019, ["PC", "PS5"], ["Role-playing (RPG)"],
                "Un detective senza memoria in una città che cade a pezzi."),
    CatalogGame(10, "Baldur's Gate 3", None, 2023, ["PC", "PS5"], ["Role-playing (RPG)", "Strategy"],
                "Un gioco di ruolo basato su Dungeons & Dragons."),
    CatalogGame(11, "Grand Theft Auto VI", None, 2026, ["PS5", "Xbox Series X|S"], ["Shooter", "Adventure"],
                "Ritorno a Vice City."),
    CatalogGame(12, "The Witcher 4", None, None, ["PC"], ["Role-playing (RPG)"],
                "Ciri è la protagonista del nuovo capitolo della saga."),
]


class FakeCatalog:
    """Catalogo di prova, senza internet: serve per i test e finché IGDB non è configurato."""

    is_demo = True

    def __init__(self, games: list[CatalogGame] | None = None) -> None:
        self.games = games if games is not None else DEMO_GAMES

    def search(self, text: str) -> list[CatalogGame]:
        """Restituisce i giochi il cui titolo contiene il testo (maiuscole ignorate)."""
        query = text.strip().lower()
        return [game for game in self.games if query in game.title.lower()]

    def trending(self) -> list[CatalogGame]:
        """Restituisce i primi giochi dell'elenco."""
        return self.games[:6]

    def new_releases(self) -> list[CatalogGame]:
        """Restituisce i giochi più recenti già usciti."""
        released = [game for game in self.games if game.release_year is not None]
        return sorted(released, key=lambda game: game.release_year or 0, reverse=True)[:6]

    def upcoming(self) -> list[CatalogGame]:
        """Restituisce gli ultimi giochi dell'elenco."""
        return self.games[-4:]

    def details(self, igdb_id: int) -> CatalogGame | None:
        """Restituisce il gioco con quell'id, oppure None."""
        for game in self.games:
            if game.igdb_id == igdb_id:
                return game
        return None


def find_library_game(games: list[Game], catalog_game: CatalogGame) -> Game | None:
    """Restituisce il gioco della libreria che corrisponde a quello del catalogo: prima per id IGDB, poi per titolo."""
    for game in games:
        if game.igdb_id == catalog_game.igdb_id:
            return game
    index = find_game_index_by_title(games, catalog_game.title)
    if index is not None and games[index].igdb_id is None:
        return games[index]
    return None


def link_to_catalog(game: Game, catalog_game: CatalogGame) -> None:
    """Collega un gioco della libreria al catalogo, copiando id IGDB e copertina."""
    game.igdb_id = catalog_game.igdb_id
    game.cover_url = catalog_game.cover_url


def link_library_game(games: list[Game], game: Game, catalog_game: CatalogGame) -> str | None:
    """Collega un gioco già in libreria al gioco IGDB scelto; restituisce un messaggio d'errore oppure None.

    Il titolo diventa quello ufficiale di IGDB, a meno che un altro gioco della libreria non lo usi già.
    Le partite e il voto restano quelli del gioco.
    """
    for other in games:
        if other is not game and other.igdb_id == catalog_game.igdb_id:
            return f"«{catalog_game.title}» è già collegato a «{other.title}» nella tua libreria."
    title_taken = any(other is not game and other.title.lower() == catalog_game.title.lower() for other in games)
    if not title_taken:
        game.title = catalog_game.title
    link_to_catalog(game, catalog_game)
    return None


def game_from_catalog(catalog_game: CatalogGame) -> Game:
    """Restituisce un nuovo gioco da mettere in libreria, ancora da giocare."""
    game = Game(catalog_game.title)
    link_to_catalog(game, catalog_game)
    return game
