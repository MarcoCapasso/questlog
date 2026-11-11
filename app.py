"""Punto di ingresso dell'app desktop di Questlog."""

import sys

from PySide6.QtWidgets import QApplication

from core.catalog import FakeCatalog, GameCatalog
from core.config import load_igdb_credentials
from core.igdb import IgdbCatalog
from core.repository import JsonGameRepository
from ui.main_window import MainWindow
from ui.theme import load_stylesheet


def create_catalog() -> GameCatalog:
    """Restituisce il catalogo IGDB se le credenziali sono nel file .env, altrimenti quello di prova."""
    credentials = load_igdb_credentials()
    if credentials is None:
        return FakeCatalog()
    client_id, client_secret = credentials
    return IgdbCatalog(client_id, client_secret)


def main() -> None:
    """Crea l'applicazione, mostra la finestra principale e avvia il ciclo di eventi."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(load_stylesheet())
    window = MainWindow(JsonGameRepository(), create_catalog())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
