"""Statistiche sulla libreria calcolate con pandas."""

import math
import pandas as pd

from csv_io import CSV_FIELDS, games_to_rows
from models import Game


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