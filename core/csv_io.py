"""Esportazione e importazione della libreria in formato CSV."""

import csv
import math
from datetime import date, datetime
from pathlib import Path

from core.library import (
    MAX_RATING,
    PLAYTHROUGH_STATUSES,
    find_game_index_by_title,
    is_valid_date_order,
    is_valid_rating,
)
from core.models import Game, Playthrough
from core.platforms import normalize_platform
from core.storage import DATA_DIR

REQUIRED_FIELDS = ["title", "rating", "platform", "status", "hours_played", "start_date", "completion_date"]
CSV_FIELDS = REQUIRED_FIELDS + ["notes", "igdb_id", "cover_url"]
CSV_FILE = DATA_DIR / "questlog_export.csv"


def export_csv(games: list[Game], path: Path = CSV_FILE) -> None:
    """Scrive la libreria nel file CSV indicato, una riga per partita."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(games_to_rows(games))


def games_to_rows(games: list[Game]) -> list[dict]:
    """Restituisce una riga per partita; i giochi in backlog occupano una riga senza dati di partita."""
    rows = []
    for game in games:
        game_cells = {
            "title": game.title,
            "rating": game.rating,
            "igdb_id": game.igdb_id,
            "cover_url": game.cover_url,
        }
        if len(game.playthroughs) == 0:
            rows.append(dict(game_cells))
        for playthrough in game.playthroughs:
            row = dict(game_cells)
            row["platform"] = playthrough.platform
            row["status"] = playthrough.status
            row["hours_played"] = playthrough.hours_played
            row["start_date"] = playthrough.start_date
            row["completion_date"] = playthrough.completion_date
            row["notes"] = playthrough.notes
            rows.append(row)
    return rows


def import_csv(today: str, path: Path = CSV_FILE) -> list[Game]:
    """Legge il file CSV indicato e restituisce i giochi; solleva ValueError se il file non è valido.

    Le colonne "notes", "igdb_id" e "cover_url" sono facoltative,
    così si possono ancora importare i CSV esportati dalle versioni precedenti.
    """
    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=";")
        if reader.fieldnames is None or not set(REQUIRED_FIELDS).issubset(reader.fieldnames):
            raise ValueError(f"Intestazione non valida: servono le colonne {', '.join(REQUIRED_FIELDS)}.")
        return rows_to_games(list(reader), today)


def rows_to_games(rows: list[dict], today: str) -> list[Game]:
    """Ricostruisce i giochi dalle righe, unendo le partite con lo stesso titolo."""
    games: list[Game] = []
    for line_number, row in enumerate(rows, start=2):
        try:
            add_row_to_games(games, row, today)
        except ValueError as error:
            raise ValueError(f"Riga {line_number}: {error}") from None
    return games


def add_row_to_games(games: list[Game], row: dict, today: str) -> None:
    """Aggiunge a games il gioco della riga, o la sua partita se il gioco esiste già."""
    title = read_cell(row, "title")
    if title == "":
        raise ValueError("il titolo è vuoto.")
    rating = parse_rating(read_cell(row, "rating"))

    game_index = find_game_index_by_title(games, title)
    if game_index is None:
        igdb_id = parse_igdb_id(read_cell(row, "igdb_id"))
        game = Game(title, rating, igdb_id=igdb_id, cover_url=read_cell(row, "cover_url") or None)
        games.append(game)
    else:
        game = games[game_index]
        if game.rating != rating:
            raise ValueError(f"'{title}' ha voti diversi su righe diverse.")

    if read_cell(row, "platform") == "":
        if rating is not None:
            raise ValueError(f"'{title}' non ha partite, quindi non può avere un voto.")
        return
    game.playthroughs.append(row_to_playthrough(row, today))


def row_to_playthrough(row: dict, today: str) -> Playthrough:
    """Crea una partita dalla riga, controllando stato, ore e date."""
    status = read_cell(row, "status").lower()
    if status not in PLAYTHROUGH_STATUSES:
        raise ValueError(f"stato '{status}' non valido (ammessi: {', '.join(PLAYTHROUGH_STATUSES)}).")

    hours_played = parse_number(read_cell(row, "hours_played"))
    if hours_played < 0:
        raise ValueError("le ore non possono essere negative.")
    if hours_played == 0 and status == "completed":
        raise ValueError("una partita completata deve avere delle ore.")

    start_date = parse_date(read_cell(row, "start_date"), today)
    completion_date = parse_date(read_cell(row, "completion_date"), today)
    if completion_date is not None and status != "completed":
        raise ValueError("solo una partita completata può avere la data di completamento.")
    if not is_valid_date_order(start_date, completion_date):
        raise ValueError("la data di completamento precede la data di inizio.")

    notes = read_cell(row, "notes")
    platform = normalize_platform(read_cell(row, "platform"))
    return Playthrough(platform, status, hours_played, start_date, completion_date, notes)


def parse_igdb_id(text: str) -> int | None:
    """Converte l'id IGDB della cella; None se la cella è vuota."""
    if text == "":
        return None
    if not text.isdigit():
        raise ValueError(f"id IGDB '{text}' non valido.")
    return int(text)


def read_cell(row: dict, field: str) -> str:
    """Restituisce il testo della cella senza spazi ai bordi; stringa vuota se la cella manca."""
    value = row.get(field)
    if value is None:
        return ""
    return value.strip()


def parse_number(text: str) -> float:
    """Converte un numero scritto con il punto o con la virgola decimale."""
    try:
        number = float(text.replace(",", "."))
    except ValueError:
        raise ValueError(f"'{text}' non è un numero valido.") from None
    if not math.isfinite(number):
        raise ValueError(f"'{text}' non è un numero valido.")
    return number


def parse_rating(text: str) -> float | None:
    """Converte il voto della cella; None se la cella è vuota."""
    if text == "":
        return None
    rating = parse_number(text)
    if not is_valid_rating(rating):
        raise ValueError(f"voto '{text}' non valido (intero da 1 a {MAX_RATING}).")
    return rating


def parse_date(text: str, today: str) -> str | None:
    """Converte una data AAAA-MM-GG o GG/MM/AAAA in formato ISO; None se la cella è vuota."""
    if text == "":
        return None
    try:
        iso_date = date.fromisoformat(text).isoformat()
    except ValueError:
        try:
            iso_date = datetime.strptime(text, "%d/%m/%Y").date().isoformat()
        except ValueError:
            raise ValueError(f"data '{text}' non valida (usa AAAA-MM-GG o GG/MM/AAAA).") from None
    if iso_date > today:
        raise ValueError(f"la data '{text}' è nel futuro.")
    return iso_date
