"""Dove Questlog trova i propri file e dove salva quelli dell'utente: da sorgente e come .exe.

Da sorgente (python app.py) tutto resta nella cartella del progetto, come sempre.
Come .exe creato da PyInstaller:
- i file dell'app (stile, icone, font, impostazioni del build) sono nella cartella del pacchetto;
- i dati dell'utente (sessione, cache) vanno in %LOCALAPPDATA%\\Questlog, l'unico posto in cui
  un programma può sempre scrivere, anche se è installato in C:\\Program Files.
"""

import os
import sys
from pathlib import Path

APP_NAME = "Questlog"
PROJECT_DIR = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    """True quando l'app gira come .exe creato da PyInstaller (che imposta sys.frozen)."""
    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """Cartella dei file che fanno parte dell'app: quella del pacchetto nell'.exe, il progetto da sorgente."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", PROJECT_DIR))
    return PROJECT_DIR


def user_data_dir() -> Path:
    """Cartella dei dati dell'utente: %LOCALAPPDATA%\\Questlog nell'.exe, "data" da sorgente."""
    if not is_frozen():
        return Path("data")
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / APP_NAME
