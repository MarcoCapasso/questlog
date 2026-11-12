"""Caricamento del foglio di stile e dei font, e posizione delle icone dell'app desktop."""

from pathlib import Path

from PySide6.QtGui import QFontDatabase

UI_DIR = Path(__file__).parent
STYLE_FILE = UI_DIR / "style.qss"
ICONS_DIR = UI_DIR / "icons"
FONTS_DIR = UI_DIR / "fonts"


def load_stylesheet() -> str:
    """Restituisce il foglio di stile QSS con i percorsi delle icone già completati."""
    stylesheet = STYLE_FILE.read_text(encoding="utf-8")
    return stylesheet.replace("{icons}", ICONS_DIR.as_posix())


def load_fonts() -> None:
    """Registra i font della cartella ui/fonts (come Google Sans per il bottone di Google), senza installarli."""
    for font_file in sorted(FONTS_DIR.glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(font_file))
