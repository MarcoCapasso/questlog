import pytest

from core.csv_io import export_csv, games_to_rows, import_csv, rows_to_games
from core.models import Game, Playthrough


TODAY = "2026-03-20"


def make_row(**cells: str) -> dict:
    row = {"title": "Hades", "rating": "", "platform": "PC", "status": "playing",
           "hours_played": "10", "start_date": "", "completion_date": ""}
    row.update(cells)
    return row


def test_games_to_rows_writes_one_row_per_playthrough():
    game = Game("Hades", 4, [Playthrough("PC", "completed", 40), Playthrough("Switch", "playing", 5)])

    rows = games_to_rows([game])

    assert len(rows) == 2
    assert rows[0]["title"] == rows[1]["title"] == "Hades"


def test_games_to_rows_writes_backlog_game_without_playthrough_data():
    rows = games_to_rows([Game("Celeste")])

    assert len(rows) == 1
    assert "platform" not in rows[0]


def test_rows_with_same_title_become_one_game():
    rows = [make_row(platform="PC"), make_row(title="hades", platform="Switch")]

    games = rows_to_games(rows, TODAY)

    assert len(games) == 1
    assert len(games[0].playthroughs) == 2


def test_row_without_platform_becomes_backlog_game():
    games = rows_to_games([make_row(platform="", status="", hours_played="")], TODAY)

    assert games == [Game("Hades")]


def test_import_accepts_comma_decimals_and_italian_dates():
    row = make_row(hours_played="2,5", start_date="05/01/2026")

    playthrough = rows_to_games([row], TODAY)[0].playthroughs[0]

    assert playthrough.hours_played == 2.5
    assert playthrough.start_date == "2026-01-05"


def test_import_error_reports_line_number():
    rows = [make_row(), make_row(status="finito")]

    with pytest.raises(ValueError, match="Riga 3"):
        rows_to_games(rows, TODAY)


def test_import_rejects_different_ratings_for_same_game():
    rows = [make_row(rating="3"), make_row(rating="4", platform="Switch")]

    with pytest.raises(ValueError, match="voti diversi"):
        rows_to_games(rows, TODAY)


def test_import_rejects_rating_on_backlog_game():
    with pytest.raises(ValueError, match="non può avere un voto"):
        rows_to_games([make_row(rating="4", platform="")], TODAY)


def test_import_rejects_future_date():
    with pytest.raises(ValueError, match="futuro"):
        rows_to_games([make_row(start_date="2026-03-21")], TODAY)


def test_export_then_import_returns_same_library(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    games = [
        Game("Zelda: Ocarina of Time; Master Quest", 5,
             [Playthrough("Switch", "completed", 30, "2026-01-01", "2026-02-01")]),
        Game("Celeste"),
    ]

    export_csv(games)

    assert import_csv(TODAY) == games
