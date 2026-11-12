"""Accesso alla libreria di giochi, indipendente da dove sono salvati i dati."""

from typing import Protocol

from core.models import Game
from core.storage import load_library, save_library


class GameRepository(Protocol):
    """Qualsiasi oggetto che sa caricare e salvare l'intera libreria."""

    def load_games(self) -> list[Game]:
        """Restituisce tutti i giochi della libreria."""
        ...

    def save_games(self, games: list[Game]) -> None:
        """Salva l'intera libreria."""
        ...


class JsonGameRepository:
    """Libreria salvata nel file JSON locale."""

    def load_games(self) -> list[Game]:
        """Restituisce i giochi letti dal file JSON."""
        return load_library()

    def save_games(self, games: list[Game]) -> None:
        """Scrive i giochi nel file JSON."""
        save_library(games)


class InMemoryGameRepository:
    """Libreria tenuta solo in memoria, utile per i test e le prove."""

    def __init__(self, games: list[Game] | None = None) -> None:
        self.games = games if games is not None else []

    def load_games(self) -> list[Game]:
        """Restituisce una copia della lista dei giochi."""
        return list(self.games)

    def save_games(self, games: list[Game]) -> None:
        """Sostituisce i giochi in memoria."""
        self.games = list(games)