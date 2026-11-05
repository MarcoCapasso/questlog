"""Modello dati di un gioco della libreria."""

from dataclasses import dataclass


@dataclass
class Game:
    """Un gioco della libreria con stato e ore giocate."""
    title: str
    platform: str
    status: str
    hours_played: float
    rating: float | None = None
    start_date: str | None = None
    completion_date: str | None = None

