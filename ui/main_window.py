"""Finestra principale di Questlog."""

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.catalog import CatalogGame, GameCatalog
from core.cloud import CloudUser
from core.models import Game
from core.repository import GameRepository
from core.storage import LIBRARY_FILE, load_library
from core.translation import NoTranslator, Translator
from ui.auth_page import AuthPage
from ui.avatar import AvatarButton
from ui.catalog_page import CatalogPage
from ui.cloud_library import CloudAccount
from ui.data_page import DataPage
from ui.game_page import GamePage
from ui.home_page import HomePage
from ui.library_page import LibraryPage
from ui.loading_page import LoadingPage
from ui.settings_page import SettingsPage
from ui.statistics_page import StatisticsPage
from ui.tasks import run_in_background
from ui.upload_page import UploadPage

HOME_NAV_INDEX = 0
LIBRARY_NAV_INDEX = 1
STATISTICS_NAV_INDEX = 2
STATUS_DURATION_MS = 6000


class MainWindow(QMainWindow):
    """La finestra principale: barra di navigazione in alto e, sotto, una pagina alla volta.

    Con un account (Supabase configurato) si entra solo dopo il login: la libreria è quella dell'account.
    Senza, l'app usa la libreria del file locale, come prima.
    """

    def __init__(
        self,
        repository: GameRepository,
        catalog: GameCatalog,
        translator: Translator,
        account: CloudAccount | None = None,
    ) -> None:
        super().__init__()
        self.account = account
        self.signed_in_user: CloudUser | None = None
        self.setWindowTitle("Questlog")
        screen_area = self.screen().availableGeometry()
        self.resize(int(screen_area.width() * 0.7), int(screen_area.height() * 0.75))
        self.setMinimumSize(960, 600)

        self.home_page = HomePage(repository, catalog)
        self.library_page = LibraryPage(repository)
        self.statistics_page = StatisticsPage(repository)
        self.settings_page = SettingsPage(
            catalog.is_demo, not isinstance(translator, NoTranslator), cloud_enabled=account is not None
        )
        self.data_page = DataPage(repository)
        self.data_page.library_replaced.connect(self.library_page.refresh)
        self.data_page.library_replaced.connect(self.home_page.refresh)
        self.catalog_page = CatalogPage(catalog, repository)
        self.game_page = GamePage(repository, catalog, translator)
        self.auth_page = AuthPage(account.auth) if account is not None else None
        if self.auth_page is not None:
            self.auth_page.signed_in.connect(self.on_signed_in)
        self.loading_page = LoadingPage()
        self.loading_page.retry_requested.connect(self.load_library)
        self.upload_page = UploadPage(account.library.remote) if account is not None else None
        if self.upload_page is not None:
            self.upload_page.done.connect(self.enter_library)
        if account is not None:
            account.library.sync_failed.connect(self.show_status)
        self.page_before_game: QWidget = self.library_page
        self.linking = False

        self.home_page.game_selected.connect(self.show_library_game)
        self.home_page.update_requested.connect(self.show_playthrough_update)
        self.home_page.library_requested.connect(self.show_library_page)
        self.home_page.add_requested.connect(self.show_catalog_page)
        self.library_page.add_requested.connect(self.show_catalog_page)
        self.library_page.game_selected.connect(self.show_library_game)
        self.catalog_page.back_requested.connect(self.go_back_from_catalog)
        self.catalog_page.game_selected.connect(self.show_catalog_game)
        self.game_page.back_requested.connect(self.go_back_from_game)
        self.game_page.library_changed.connect(self.library_page.refresh)
        self.game_page.library_changed.connect(self.home_page.refresh)
        self.game_page.link_requested.connect(self.show_link_catalog)

        self.pages = QStackedWidget()
        self.nav_buttons = QButtonGroup(self)
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 14, 40, 14)
        header_layout.setSpacing(6)
        logo = QLabel("QUESTLOG")
        logo.setObjectName("logo")
        header_layout.addWidget(logo)

        pages = [
            ("Home", self.home_page),
            ("Libreria", self.library_page),
            ("Statistiche", self.statistics_page),
        ]
        for index, (name, page) in enumerate(pages):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setCheckable(True)
            self.nav_buttons.addButton(button, index)
            header_layout.addWidget(button)
            self.pages.addWidget(page)
        header_layout.addStretch()
        self.status_label = QLabel()
        self.status_label.setObjectName("statusMessage")
        self.status_label.hide()
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.status_label.hide)
        header_layout.addWidget(self.status_label)
        header_layout.addSpacing(12)
        self.avatar = AvatarButton()
        self.avatar.settings_requested.connect(lambda: self.show_page(self.settings_page))
        self.avatar.data_requested.connect(self.show_data_page)
        self.avatar.login_requested.connect(self.show_auth_page)
        self.avatar.logout_requested.connect(self.start_logout)
        self.avatar.set_login_available(account is not None)
        header_layout.addWidget(self.avatar)
        # Schermo intero: dal menu dell'avatar o con F11; Esc ne esce.
        # L'azione va aggiunta anche alla finestra, altrimenti F11 funzionerebbe solo a menu aperto.
        self.addAction(self.avatar.fullscreen_action)
        self.avatar.fullscreen_action.toggled.connect(self.set_fullscreen)
        self.exit_fullscreen_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.exit_fullscreen_shortcut.activated.connect(lambda: self.set_fullscreen(False))
        self.exit_fullscreen_shortcut.setEnabled(False)
        self.was_maximized = False
        extra_pages = (
            self.catalog_page,
            self.game_page,
            self.settings_page,
            self.data_page,
            self.auth_page,
            self.loading_page,
            self.upload_page,
        )
        for extra_page in extra_pages:
            if extra_page is not None:
                self.pages.addWidget(extra_page)

        self.nav_buttons.idClicked.connect(self.show_nav_page)
        self.nav_buttons.button(HOME_NAV_INDEX).setChecked(True)
        if account is None:
            self.home_page.refresh()
        else:
            self.set_navigation_visible(False)
            self.show_page(self.loading_page)
            run_in_background(account.auth.current_user, self.on_session_checked, self.on_session_check_failed)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(header)
        central_layout.addWidget(self.pages)
        self.setCentralWidget(central)

    def set_fullscreen(self, fullscreen: bool) -> None:
        """Entra o esce dallo schermo intero; uscendo torna com'era prima (ingrandita o no)."""
        if fullscreen == self.isFullScreen():
            return
        if fullscreen:
            self.was_maximized = self.isMaximized()
            self.showFullScreen()
        elif self.was_maximized:
            self.showMaximized()
        else:
            self.showNormal()

    def changeEvent(self, event: QEvent) -> None:
        """Tiene allineati la spunta nel menu e il tasto Esc con lo stato reale della finestra."""
        if event.type() == QEvent.Type.WindowStateChange:
            fullscreen = self.isFullScreen()
            self.avatar.fullscreen_action.setChecked(fullscreen)
            self.exit_fullscreen_shortcut.setEnabled(fullscreen)
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Alla chiusura: smette di aspettare il browser e salva online le ultime modifiche."""
        if self.account is not None:
            self.account.auth.cancel_waiting()
            self.account.library.flush()
        super().closeEvent(event)

    def show_page(self, page: QWidget) -> None:
        """Mostra una pagina ed evidenzia il bottone in alto giusto.

        Il gioco evidenzia il bottone della pagina da cui è stato aperto, il catalogo quello della Libreria.
        Impostazioni, dati, accesso e attesa non sono nella barra: nessun bottone resta evidenziato.
        """
        self.pages.setCurrentWidget(page)
        if page in (self.settings_page, self.data_page, self.auth_page, self.loading_page, self.upload_page):
            self.nav_buttons.setExclusive(False)
            for button in self.nav_buttons.buttons():
                button.setChecked(False)
            self.nav_buttons.setExclusive(True)
            return
        section = self.page_before_game if page is self.game_page else page
        nav_index = HOME_NAV_INDEX if section is self.home_page else LIBRARY_NAV_INDEX
        self.nav_buttons.button(nav_index).setChecked(True)

    def show_status(self, text: str) -> None:
        """Mostra un breve messaggio in alto a destra, che sparisce da solo dopo qualche secondo."""
        self.status_label.setText(text)
        self.status_label.show()
        self.status_timer.start(STATUS_DURATION_MS)

    def set_navigation_visible(self, visible: bool) -> None:
        """Mostra o nasconde Home, Libreria e Statistiche: senza login non si vede nessuna libreria."""
        for button in self.nav_buttons.buttons():
            button.setVisible(visible)

    def show_auth_page(self) -> None:
        """Apre la pagina Accedi / Registrati."""
        if self.auth_page is not None:
            self.show_page(self.auth_page)

    def on_session_checked(self, user: CloudUser | None) -> None:
        """All'avvio: con una sessione salvata si entra subito, altrimenti si chiede il login."""
        if user is None:
            self.show_auth_page()
        else:
            self.on_signed_in(user)

    def on_session_check_failed(self, _message: str) -> None:
        """All'avvio, senza rete, non si sa chi sei: si mostra la pagina di accesso."""
        self.show_auth_page()

    def on_signed_in(self, user: CloudUser) -> None:
        """Login riuscito: aggiorna l'avatar e scarica la libreria dell'account."""
        self.avatar.set_user(user)
        self.signed_in_user = user
        self.load_library()

    def load_library(self) -> None:
        """Scarica la libreria dell'account in background, mostrando la pagina d'attesa."""
        if self.account is None:
            return
        self.loading_page.show_message("Carico la tua libreria…")
        self.show_page(self.loading_page)
        run_in_background(self.account.library.remote.fetch_games, self.on_library_loaded, self.on_library_failed)

    def on_library_loaded(self, games: list[Game]) -> None:
        """Libreria arrivata. Se l'account è vuoto e su questo PC c'è una libreria, propone di caricarla."""
        local_games = load_library() if not games and LIBRARY_FILE.exists() else []
        if local_games and self.upload_page is not None:
            self.upload_page.start(local_games)
            self.show_page(self.upload_page)
            return
        self.enter_library(games)

    def enter_library(self, games: list[Game]) -> None:
        """Si entra: la libreria dell'account diventa quella delle pagine e si apre la Home."""
        if self.account is None:
            return
        self.account.library.set_games(games)
        self.set_navigation_visible(True)
        self.library_page.refresh()
        self.home_page.refresh()
        self.show_page(self.home_page)
        if self.signed_in_user is not None:
            self.show_status(f"Ciao, {self.signed_in_user.name.split()[0]}!")

    def on_library_failed(self, message: str) -> None:
        """Libreria non scaricata (per esempio senza rete): lo dice e propone di riprovare."""
        self.loading_page.show_error(message)
        self.show_page(self.loading_page)

    def start_logout(self) -> None:
        """Salva le ultime modifiche, poi esce dall'account in background."""
        if self.account is None:
            return
        self.account.library.flush()
        run_in_background(self.account.auth.sign_out, self.on_signed_out, self.on_signed_out)

    def on_signed_out(self, _result: object = None) -> None:
        """Dopo il logout (anche se il server non ha risposto, la sessione locale è cancellata)."""
        if self.account is not None:
            self.account.library.clear()
        if self.auth_page is not None:
            self.auth_page.start()
        self.signed_in_user = None
        self.avatar.set_user(None)
        self.set_navigation_visible(False)
        self.library_page.refresh()
        self.home_page.refresh()
        self.show_auth_page()
        self.show_status("Sei uscito dall'account.")

    def show_data_page(self) -> None:
        """Apre la pagina di import ed export, ripulita da messaggi vecchi."""
        self.data_page.start()
        self.show_page(self.data_page)

    def show_nav_page(self, nav_index: int) -> None:
        """Mostra la pagina del bottone cliccato in alto; Home e Statistiche si aggiornano prima di comparire."""
        if nav_index == HOME_NAV_INDEX:
            self.home_page.refresh()
        elif nav_index == STATISTICS_NAV_INDEX:
            self.statistics_page.refresh()
        self.pages.setCurrentIndex(nav_index)

    def show_library_page(self) -> None:
        """Torna alla libreria."""
        self.show_page(self.library_page)

    def show_catalog_page(self) -> None:
        """Apre il catalogo per scegliere un gioco da aggiungere."""
        self.linking = False
        self.catalog_page.start()
        self.show_page(self.catalog_page)

    def show_link_catalog(self, title: str) -> None:
        """Apre il catalogo per scegliere a quale gioco IGDB collegare il gioco mostrato."""
        self.linking = True
        self.catalog_page.start(link_title=title)
        self.show_page(self.catalog_page)

    def go_back_from_catalog(self) -> None:
        """Dal catalogo si torna al gioco se lo si stava collegando, altrimenti alla libreria."""
        if self.linking:
            self.linking = False
            self.show_page(self.game_page)
        else:
            self.show_library_page()

    def show_catalog_game(self, catalog_game: CatalogGame) -> None:
        """Apre la pagina di un gioco scelto nel catalogo, oppure lo usa per collegare il gioco mostrato."""
        if self.linking:
            self.linking = False
            self.game_page.link_game(catalog_game)
            self.show_page(self.game_page)
            return
        self.page_before_game = self.catalog_page
        self.game_page.show_catalog_game(catalog_game)
        self.show_page(self.game_page)

    def show_library_game(self, game: Game) -> None:
        """Apre la pagina di un gioco della libreria; "Indietro" riporta alla pagina da cui lo si è aperto."""
        current_page = self.pages.currentWidget()
        self.page_before_game = self.home_page if current_page is self.home_page else self.library_page
        self.game_page.show_library_game(game)
        self.show_page(self.game_page)

    def show_playthrough_update(self, game: Game, playthrough_index: int) -> None:
        """Dalla Home: apre il gioco in corso con la sua partita già aperta in modifica."""
        self.show_library_game(game)
        self.game_page.open_playthrough_form(playthrough_index)

    def go_back_from_game(self) -> None:
        """Torna alla pagina da cui si era aperto il gioco, aggiornandola."""
        if self.page_before_game is self.catalog_page:
            self.catalog_page.refresh_cards()
        self.show_page(self.page_before_game)
