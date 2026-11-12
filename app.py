"""Punto di ingresso dell'app desktop di Questlog."""

import sys

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from core.catalog import FakeCatalog, GameCatalog
from core.cloud import AuthService, create_supabase_client
from core.cloud_repository import SupabaseGameRepository
from core.config import load_deepl_api_key, load_igdb_credentials, load_supabase_settings
from core.igdb import IgdbCatalog
from core.repository import GameRepository, JsonGameRepository
from core.translation import DeepLTranslator, NoTranslator, Translator
from ui.cloud_library import CloudAccount, CloudLibrary
from ui.main_window import MainWindow
from ui.theme import load_fonts, load_stylesheet


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


def create_account() -> CloudAccount | None:
    """Restituisce login e libreria online se Supabase è configurato nel file .env, altrimenti None.

    Login e libreria usano lo stesso client: dopo il login, le richieste al database partono già come quell'utente.
    """
    settings = load_supabase_settings()
    if settings is None:
        return None
    url, key = settings
    client = create_supabase_client(url, key)
    return CloudAccount(AuthService(client), CloudLibrary(SupabaseGameRepository(client)))


def main() -> None:
    """Crea l'applicazione, mostra la finestra principale e avvia il ciclo di eventi."""
    QLocale.setDefault(QLocale(QLocale.Language.Italian, QLocale.Country.Italy))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_fonts()
    app.setStyleSheet(load_stylesheet())
    account = create_account()
    repository: GameRepository = account.library if account is not None else JsonGameRepository()
    window = MainWindow(repository, create_catalog(), create_translator(), account)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
