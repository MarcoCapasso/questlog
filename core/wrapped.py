"""Il riepilogo "alla Spotify Wrapped": i numeri e le classifiche che raccontano come giochi, anche anno per anno."""

from dataclasses import dataclass, replace
from datetime import date
from statistics import median

from core.models import Game, Playthrough

TOP_GAMES_LIMIT = 5
LOYAL_SHARE = 0.5
COMPLETIONIST_RATE = 0.8
EXPLORER_GAMES = 8


@dataclass
class GameHours:
    """Un gioco con le ore che gli hai dedicato nel periodo considerato."""
    game: Game
    hours: float


@dataclass
class Profile:
    """Il "tipo di giocatore" che emerge dai numeri, con una frase che lo spiega."""
    title: str
    description: str


@dataclass
class WrappedStats:
    """Tutti i numeri della pagina Statistiche; None dove non c'è abbastanza da raccontare."""
    total_hours: float
    games_played: int
    top_games: list[GameHours]
    platform_hours: list[tuple[str, float]]
    playing: int
    completed: int
    dropped: int
    completion_rate: float | None
    average_rating: float | None
    favorite_game: Game | None
    median_days: float | None
    fastest: tuple[Game, int] | None
    profile: Profile | None


def playthrough_year(playthrough: Playthrough) -> int | None:
    """Restituisce l'anno a cui appartiene una partita: quello di completamento, altrimenti quello di inizio."""
    date_text = playthrough.completion_date or playthrough.start_date
    return int(date_text[:4]) if date_text is not None else None


def activity_years(games: list[Game]) -> list[int]:
    """Restituisce gli anni in cui hai giocato, dal più recente."""
    years = {
        year
        for game in games
        for playthrough in game.playthroughs
        if (year := playthrough_year(playthrough)) is not None
    }
    return sorted(years, reverse=True)


def games_in_year(games: list[Game], year: int | None) -> list[Game]:
    """Restituisce i giochi con le sole partite di quell'anno; con None restituisce tutti i giochi giocati.

    Crea copie con dataclasses.replace: la libreria originale non viene mai modificata.
    """
    result = []
    for game in games:
        playthroughs = [
            playthrough
            for playthrough in game.playthroughs
            if year is None or playthrough_year(playthrough) == year
        ]
        if playthroughs:
            result.append(replace(game, playthroughs=playthroughs))
    return result


def compute_wrapped(games: list[Game], year: int | None = None) -> WrappedStats:
    """Calcola tutti i numeri della pagina Statistiche per un anno, oppure per sempre (year=None)."""
    played = games_in_year(games, year)
    hours_by_game = sorted(
        (GameHours(game, sum(p.hours_played for p in game.playthroughs)) for game in played),
        key=lambda item: item.hours,
        reverse=True,
    )
    total_hours = sum(item.hours for item in hours_by_game)
    playthroughs = [playthrough for game in played for playthrough in game.playthroughs]
    completed = sum(1 for p in playthroughs if p.status == "completed")
    dropped = sum(1 for p in playthroughs if p.status == "dropped")
    concluded = completed + dropped
    ratings = [game.rating for game in played if game.rating is not None]
    durations = completion_durations(played)

    return WrappedStats(
        total_hours=total_hours,
        games_played=len(played),
        top_games=hours_by_game[:TOP_GAMES_LIMIT],
        platform_hours=platform_hours(playthroughs),
        playing=sum(1 for p in playthroughs if p.status == "playing"),
        completed=completed,
        dropped=dropped,
        completion_rate=completed / concluded if concluded else None,
        average_rating=sum(ratings) / len(ratings) if ratings else None,
        favorite_game=favorite_game(hours_by_game),
        median_days=median(days for _, days in durations) if durations else None,
        fastest=min(durations, key=lambda item: item[1]) if durations else None,
        profile=choose_profile(hours_by_game, total_hours, completed, concluded),
    )


def platform_hours(playthroughs: list[Playthrough]) -> list[tuple[str, float]]:
    """Restituisce le ore per piattaforma, dalla più giocata."""
    totals: dict[str, float] = {}
    for playthrough in playthroughs:
        totals[playthrough.platform] = totals.get(playthrough.platform, 0) + playthrough.hours_played
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def favorite_game(hours_by_game: list[GameHours]) -> Game | None:
    """Restituisce il gioco con il voto più alto; a parità di voto, quello a cui hai giocato di più."""
    rated = [item for item in hours_by_game if item.game.rating is not None]
    if not rated:
        return None
    best = max(rated, key=lambda item: (item.game.rating or 0, item.hours))
    return best.game


def completion_durations(games: list[Game]) -> list[tuple[Game, int]]:
    """Restituisce i giorni impiegati per ogni partita completata che ha entrambe le date."""
    durations = []
    for game in games:
        for playthrough in game.playthroughs:
            if playthrough.status == "completed" and playthrough.start_date and playthrough.completion_date:
                start = date.fromisoformat(playthrough.start_date)
                end = date.fromisoformat(playthrough.completion_date)
                durations.append((game, (end - start).days))
    return durations


def choose_profile(
    hours_by_game: list[GameHours],
    total_hours: float,
    completed: int,
    concluded: int,
) -> Profile | None:
    """Sceglie il profilo da giocatore: la prima regola che si applica vince."""
    if not hours_by_game or total_hours == 0:
        return None
    top = hours_by_game[0]
    if top.hours / total_hours >= LOYAL_SHARE:
        return Profile(
            "Il Fedelissimo",
            f"Quando un gioco ti prende non lo molli più: {top.game.title} si è preso da solo "
            f"più di metà del tuo tempo.",
        )
    if concluded and completed / concluded >= COMPLETIONIST_RATE:
        return Profile(
            "Il Completista",
            "Quello che inizi lo finisci. I titoli di coda sono il tuo habitat naturale.",
        )
    if len(hours_by_game) >= EXPLORER_GAMES:
        return Profile(
            "L'Esploratore",
            "Tanti mondi, tante avventure: preferisci assaggiare un po' di tutto.",
        )
    return Profile(
        "Lo Stratega",
        "Scegli con cura a cosa giocare e ti godi ogni partita con calma.",
    )
