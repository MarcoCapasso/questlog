"""Crea la versione di Questlog per Windows: dist/Questlog/Questlog.exe e lo zip da pubblicare.

Uso, dalla cartella del progetto con il venv attivo:
    python build.py
"""

import shutil
import sys
from pathlib import Path

import PyInstaller.__main__

from core.config import write_bundled_settings
from core.version import APP_VERSION

PROJECT_DIR = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_DIR / "build"
DIST_DIR = PROJECT_DIR / "dist"
APP_NAME = "Questlog"
ICON_FILE = PROJECT_DIR / "ui" / "icons" / "questlog.ico"
SETTINGS_FILE = BUILD_DIR / "app_settings.json"
# File che non sono codice Python: PyInstaller non li trova da solo, vanno elencati (sorgente, destinazione).
DATA_FILES = [
    (PROJECT_DIR / "ui" / "style.qss", "ui"),
    (PROJECT_DIR / "ui" / "icons", "ui/icons"),
    (PROJECT_DIR / "ui" / "fonts", "ui/fonts"),
    (SETTINGS_FILE, "."),
]
# Librerie installate ma non usate dall'app desktop (grafici del terminale, test, extra facoltativi di pandas):
# PyInstaller le includerebbe perché "potrebbero servire", gonfiando il pacchetto di decine di MB.
EXCLUDED_MODULES = ["matplotlib", "scipy", "PIL", "lxml", "pytest", "mypy", "tkinter"]


def main() -> None:
    """Prepara le impostazioni pubbliche, lancia PyInstaller e comprime il risultato in uno zip."""
    BUILD_DIR.mkdir(exist_ok=True)
    missing = write_bundled_settings(SETTINGS_FILE)
    if missing:
        sys.exit(f"Mancano nel file .env: {', '.join(missing)}. Senza, l'exe non può collegarsi a Supabase.")

    arguments = [
        str(PROJECT_DIR / "app.py"),
        "--name", APP_NAME,
        "--windowed",
        "--noconfirm",
        "--clean",
        "--icon", str(ICON_FILE),
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / "pyinstaller"),
        "--specpath", str(BUILD_DIR),
    ]
    for source, destination in DATA_FILES:
        arguments += ["--add-data", f"{source}:{destination}"]
    for module in EXCLUDED_MODULES:
        arguments += ["--exclude-module", module]
    PyInstaller.__main__.run(arguments)

    archive_base = DIST_DIR / f"{APP_NAME}-{APP_VERSION}-windows"
    archive = shutil.make_archive(str(archive_base), "zip", root_dir=DIST_DIR, base_dir=APP_NAME)
    print(f"\nPronto: {DIST_DIR / APP_NAME / APP_NAME}.exe")
    print(f"Da pubblicare: {archive}")


if __name__ == "__main__":
    main()
