"""Modello dati di un gioco della libreria e delle sue partite."""

from dataclasses import dataclass, field


@dataclass
class Playthrough:
    """Una partita a un gioco, su una piattaforma, con stato, ore, date e note libere."""
    platform: str
    status: str
    hours_played: float
    start_date: str | None = None
    completion_date: str | None = None
    notes: str = ""


@dataclass
class Game:
    """Un gioco della libreria con voto, partite e, se arriva da IGDB, il suo id e la copertina."""
    title: str
    rating: float | None = None
    playthroughs: list[Playthrough] = field(default_factory=list)
    igdb_id: int | None = None
    cover_url: str | None = None
