"""Caricamento del foglio di stile dell'app desktop."""

from pathlib import Path

STYLE_FILE = Path(__file__).parent / "style.qss"


def load_stylesheet() -> str:
    """Restituisce il contenuto del foglio di stile QSS."""
    return STYLE_FILE.read_text(encoding="utf-8")