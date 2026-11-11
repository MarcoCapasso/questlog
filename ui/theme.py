"""Caricamento del foglio di stile e posizione delle icone dell'app desktop."""

from pathlib import Path

UI_DIR = Path(__file__).parent
STYLE_FILE = UI_DIR / "style.qss"
ICONS_DIR = UI_DIR / "icons"


def load_stylesheet() -> str:
    """Restituisce il foglio di stile QSS con i percorsi delle icone già completati."""
    stylesheet = STYLE_FILE.read_text(encoding="utf-8")
    return stylesheet.replace("{icons}", ICONS_DIR.as_posix())
