import sys
from pathlib import Path

from core.paths import PROJECT_DIR, is_frozen, resource_dir, user_data_dir


def test_from_source_everything_stays_in_the_project():
    assert not is_frozen()
    assert user_data_dir() == Path("data")
    assert resource_dir() == PROJECT_DIR


def test_as_exe_user_data_goes_to_local_app_data(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "pacchetto"), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))

    assert user_data_dir() == tmp_path / "AppData" / "Local" / "Questlog"
    assert resource_dir() == tmp_path / "pacchetto"
