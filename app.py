"""Punto di ingresso dell'app desktop di Questlog."""

import sys

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication
from supabase import Client

from core.catalog import FakeCatalog, GameCatalog
from core.cloud import AuthService, create_supabase_client
from core.cloud_repository import SupabaseGameRepository
from core.config import load_deepl_api_key, load_supabase_settings
from core.igdb import IgdbCatalog
from core.repository import GameRepository, JsonGameRepository
from core.translation import DeepLTranslator, NoTranslator, Translator
from ui.cloud_library import CloudAccount, CloudLibrary
from ui.main_window import MainWindow
from ui.theme import load_fonts, load_stylesheet


def create_supabase() -> Client | None:
    """Restituisce il client Supabase se il progetto è configurato nel file .env, altrimenti None."""
    settings = load_supabase_settings()
    if settings is None:
        return None
    url, key = settings
    return create_supabase_client(url, key)


def create_catalog(client: Client | None) -> GameCatalog:
    """Restituisce il catalogo IGDB (tramite la Edge Function di Supabase), oppure quello di prova senza Supabase."""
    if client is None:
        return FakeCatalog()
    return IgdbCatalog(client)


def create_translator() -> Translator:
    """Restituisce il traduttore DeepL se la chiave è nel file .env, altrimenti uno che lascia il testo com'è."""
    api_key = load_deepl_api_key()
    if api_key is None:
        return NoTranslator()
    return DeepLTranslator(api_key)


def create_account(client: Client) -> CloudAccount:
    """Restituisce login e libreria online.

    Login, libreria e catalogo usano lo stesso client: dopo il login, ogni richiesta parte già come quell'utente.
    """
    return CloudAccount(AuthService(client), CloudLibrary(SupabaseGameRepository(client)))


def main() -> None:
    """Crea l'applicazione, mostra la finestra principale e avvia il ciclo di eventi."""
    QLocale.setDefault(QLocale(QLocale.Language.Italian, QLocale.Country.Italy))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_fonts()
    app.setStyleSheet(load_stylesheet())
    client = create_supabase()
    account = create_account(client) if client is not None else None
    repository: GameRepository = account.library if account is not None else JsonGameRepository()
    window = MainWindow(repository, create_catalog(client), create_translator(), account)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
