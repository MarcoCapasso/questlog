"""Modello dati di un gioco della libreria e delle sue partite."""

from dataclasses import dataclass, field


@dataclass
class Playthrough:
    """Una partita a un gioco, su una piattaforma, con stato, ore e date."""
    platform: str
    status: str
    hours_played: float
    start_date: str | None = None
    completion_date: str | None = None


@dataclass
class Game:
    """Un gioco della libreria con voto e l'elenco delle sue partite."""
    title: str
    rating: float | None = None
    playthroughs: list[Playthrough] = field(default_factory=list)
