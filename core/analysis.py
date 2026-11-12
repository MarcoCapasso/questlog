"""Statistiche sulla libreria calcolate con pandas."""

import math
from dataclasses import dataclass

import pandas as pd

from core.csv_io import CSV_FIELDS, games_to_rows
from core.models import Game


def games_to_dataframe(games: list[Game]) -> pd.DataFrame:
    """Restituisce una tabella con una riga per partita, come nel CSV."""
    df = pd.DataFrame(games_to_rows(games), columns=CSV_FIELDS)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["completion_date"] = pd.to_datetime(df["completion_date"])
    return df


def playthrough_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Restituisce solo le righe delle partite, escludendo i giochi in backlog."""
    return df.dropna(subset=["platform"])


def hours_by_platform(df: pd.DataFrame) -> pd.Series:
    """Restituisce le ore totali per piattaforma, dalla più giocata."""
    hours = playthrough_rows(df).groupby("platform")["hours_played"].sum()
    return hours.sort_values(ascending=False)


def playthroughs_by_status(df: pd.DataFrame) -> pd.Series:
    """Restituisce il numero di partite per stato, dal più frequente."""
    return playthrough_rows(df)["status"].value_counts()


def hours_per_game(df: pd.DataFrame) -> pd.Series:
    """Restituisce le ore totali di ogni gioco giocato."""
    return playthrough_rows(df).groupby("title")["hours_played"].sum()


def median_hours_per_game(df: pd.DataFrame) -> float:
    """Restituisce la mediana delle ore totali dei giochi giocati."""
    return float(hours_per_game(df).median())


def days_to_complete(df: pd.DataFrame) -> pd.Series:
    """Restituisce i giorni impiegati per ogni partita completata che ha entrambe le date."""
    completed = df[df["status"] == "completed"]
    completed = completed.dropna(subset=["start_date", "completion_date"])
    return (completed["completion_date"] - completed["start_date"]).dt.days


def completions_per_year(df: pd.DataFrame) -> pd.Series:
    """Restituisce il numero di partite completate in ogni anno, in ordine cronologico."""
    completed = df[df["status"] == "completed"].dropna(subset=["completion_date"])
    return completed["completion_date"].dt.year.value_counts().sort_index()


def completion_rate(df: pd.DataFrame) -> float:
    """Restituisce la quota di partite concluse che sono state completate; NaN se nessuna è conclusa."""
    statuses = playthrough_rows(df)["status"]
    concluded = statuses[statuses.isin(["completed", "dropped"])]
    if concluded.empty:
        return math.nan
    return float((concluded == "completed").mean())


def average_rating(df: pd.DataFrame) -> float:
    """Restituisce la media dei voti dei giochi votati; NaN se nessun gioco ha un voto."""
    ratings = df.drop_duplicates(subset="title")["rating"]
    return float(ratings.mean())


@dataclass
class LibrarySummary:
    """I numeri principali della libreria, già pronti da mostrare; None dove non c'è abbastanza da calcolare."""
    total_hours: float
    completed_playthroughs: int
    completion_rate: float | None
    average_rating: float | None
    median_days_to_complete: float | None


def summarize_library(games: list[Game]) -> LibrarySummary:
    """Restituisce il riepilogo della libreria, trasformando i NaN di pandas in None."""
    df = games_to_dataframe(games)
    statuses = playthroughs_by_status(df)
    return LibrarySummary(
        total_hours=float(hours_by_platform(df).sum()),
        completed_playthroughs=int(statuses.get("completed", 0)),
        completion_rate=nan_to_none(completion_rate(df)),
        average_rating=nan_to_none(average_rating(df)),
        median_days_to_complete=nan_to_none(float(days_to_complete(df).median())),
    )


def nan_to_none(value: float) -> float | None:
    """Restituisce None al posto di NaN, il valore "non disponibile" di pandas."""
    return None if math.isnan(value) else value
