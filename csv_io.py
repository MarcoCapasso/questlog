"""Esportazione e importazione della libreria in formato CSV."""

import csv

from models import Game

CSV_FIELDS = ["title", "rating", "platform", "status", "hours_played", "start_date", "completion_date"]
EXPORT_FILE = "questlog_export.csv"


def export_csv(games: list[Game]) -> None:
    """Scrive la libreria nel file CSV, una riga per partita."""
    with open(EXPORT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(games_to_rows(games))


def games_to_rows(games: list[Game]) -> list[dict]:
    """Restituisce una riga per partita; i giochi in backlog occupano una riga senza dati di partita."""
    rows = []
    for game in games:
        if len(game.playthroughs) == 0:
            rows.append({"title": game.title, "rating": game.rating})
        for playthrough in game.playthroughs:
            row = {"title": game.title, "rating": game.rating}
            row["platform"] = playthrough.platform
            row["status"] = playthrough.status
            row["hours_played"] = playthrough.hours_played
            row["start_date"] = playthrough.start_date
            row["completion_date"] = playthrough.completion_date
            rows.append(row)
    return rows