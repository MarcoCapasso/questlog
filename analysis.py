"""Statistiche sulla libreria calcolate con pandas."""

import pandas as pd

from csv_io import CSV_FIELDS, games_to_rows
from models import Game


def games_to_dataframe(games: list[Game]) -> pd.DataFrame:
    """Restituisce una tabella con una riga per partita, come nel CSV."""
    df = pd.DataFrame(games_to_rows(games), columns=CSV_FIELDS)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["completion_date"] = pd.to_datetime(df["completion_date"])
    return df


def hours_by_platform(df: pd.DataFrame) -> pd.Series:
    """Restituisce le ore totali per piattaforma, dalla più giocata."""
    playthroughs = playthrough_rows(df)
    hours = playthroughs.groupby("platform")["hours_played"].sum()
    return hours.sort_values(ascending=False)


def playthroughs_by_status(df: pd.DataFrame) -> pd.Series:
    """Restituisce il numero di partite per stato, dal più frequente."""
    playthroughs =playthrough_rows(df)
    return playthroughs["status"].value_counts()


def playthrough_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Restituisce solo le righe delle partite, escludendo i giochi in backlog."""
    return df.dropna(subset=["platform"])


def median_hours_per_game(df: pd.DataFrame) -> float:
    """Restituisce la mediana delle ore totali dei giochi giocati."""
    hours_per_game = playthrough_rows(df).groupby("title")["hours_played"].sum()
    return float(hours_per_game.median())