import json

from core.models import Game, Playthrough
from core.storage import CORRUPTED_LIBRARY_FILE, DATA_DIR, LIBRARY_FILE, load_library, save_library


def test_save_and_load_keep_games_and_playthroughs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    games = [
        Game("Hades", 9, [Playthrough("PC", "completed", 40, "2026-01-01", "2026-02-01")]),
        Game("Celeste"),
    ]

    save_library(games)

    assert load_library() == games


def test_load_returns_empty_list_when_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert load_library() == []


def test_load_moves_old_format_to_corrupted_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / DATA_DIR).mkdir()
    old_games = [{"title": "Hades", "platform": "PC", "status": "playing", "hours_played": 10}]
    (tmp_path / LIBRARY_FILE).write_text(json.dumps(old_games), encoding="utf-8")

    assert load_library() == []
    assert (tmp_path / CORRUPTED_LIBRARY_FILE).exists()
    assert not (tmp_path / LIBRARY_FILE).exists()
