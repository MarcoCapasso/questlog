"""Punto di ingresso dell'app desktop di Questlog."""

import sys

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from core.catalog import FakeCatalog, GameCatalog
from core.config import load_deepl_api_key, load_igdb_credentials
from core.igdb import IgdbCatalog
from core.repository import JsonGameRepository
from core.translation import DeepLTranslator, NoTranslator, Translator
from ui.main_window import MainWindow
from ui.theme import load_stylesheet


def create_catalog() -> GameCatalog:
    """Restituisce il catalogo IGDB se le credenziali sono nel file .env, altrimenti quello di prova."""
    credentials = load_igdb_credentials()
    if credentials is None:
        return FakeCatalog()
    client_id, client_secret = credentials
    return IgdbCatalog(client_id, client_secret)


def create_translator() -> Translator:
    """Restituisce il traduttore DeepL se la chiave è nel file .env, altrimenti uno che lascia il testo com'è."""
    api_key = load_deepl_api_key()
    if api_key is None:
        return NoTranslator()
    return DeepLTranslator(api_key)


def main() -> None:
    """Crea l'applicazione, mostra la finestra principale e avvia il ciclo di eventi."""
    QLocale.setDefault(QLocale(QLocale.Language.Italian, QLocale.Country.Italy))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(load_stylesheet())
    window = MainWindow(JsonGameRepository(), create_catalog(), create_translator())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
