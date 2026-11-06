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