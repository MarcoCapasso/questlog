"""Finestra principale di Questlog."""

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
from core.models import Game
from core.repository import GameRepository
from core.translation import NoTranslator, Translator
from ui.avatar import AvatarButton
from ui.catalog_page import CatalogPage
from ui.data_page import DataPage
from ui.game_page import GamePage
from ui.home_page import HomePage
from ui.library_page import LibraryPage
from ui.settings_page import SettingsPage
from ui.statistics_page import StatisticsPage

HOME_NAV_INDEX = 0
LIBRARY_NAV_INDEX = 1
STATISTICS_NAV_INDEX = 2


class MainWindow(QMainWindow):
    """La finestra principale: barra di navigazione in alto e, sotto, una pagina alla volta."""

    def __init__(self, repository: GameRepository, catalog: GameCatalog, translator: Translator) -> None:
        super().__init__()
        self.setWindowTitle("Questlog")
        screen_area = self.screen().availableGeometry()
        self.resize(int(screen_area.width() * 0.7), int(screen_area.height() * 0.75))
        self.setMinimumSize(960, 600)

        self.home_page = HomePage(repository, catalog)
        self.library_page = LibraryPage(repository)
        self.statistics_page = StatisticsPage(repository)
        self.settings_page = SettingsPage(catalog.is_demo, not isinstance(translator, NoTranslator))
        self.data_page = DataPage(repository)
        self.data_page.library_replaced.connect(self.library_page.refresh)
        self.data_page.library_replaced.connect(self.home_page.refresh)
        self.catalog_page = CatalogPage(catalog, repository)
        self.game_page = GamePage(repository, catalog, translator)
        self.page_before_game: QWidget = self.library_page
        self.linking = False

        self.home_page.game_selected.connect(self.show_library_game)
        self.home_page.update_requested.connect(self.show_playthrough_update)
        self.home_page.library_requested.connect(self.show_library_page)
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
        self.avatar = AvatarButton()
        self.avatar.settings_requested.connect(lambda: self.show_page(self.settings_page))
        self.avatar.data_requested.connect(self.show_data_page)
        header_layout.addWidget(self.avatar)
        for extra_page in (self.catalog_page, self.game_page, self.settings_page, self.data_page):
            self.pages.addWidget(extra_page)

        self.nav_buttons.idClicked.connect(self.show_nav_page)
        self.nav_buttons.button(HOME_NAV_INDEX).setChecked(True)
        self.home_page.refresh()

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(header)
        central_layout.addWidget(self.pages)
        self.setCentralWidget(central)

    def show_page(self, page: QWidget) -> None:
        """Mostra una pagina ed evidenzia il bottone in alto giusto.

        Il gioco evidenzia il bottone della pagina da cui è stato aperto, il catalogo quello della Libreria.
        Impostazioni e dati si aprono dall'avatar: nessun bottone resta evidenziato.
        """
        self.pages.setCurrentWidget(page)
        if page in (self.settings_page, self.data_page):
            self.nav_buttons.setExclusive(False)
            for button in self.nav_buttons.buttons():
                button.setChecked(False)
            self.nav_buttons.setExclusive(True)
            return
        section = self.page_before_game if page is self.game_page else page
        nav_index = HOME_NAV_INDEX if section is self.home_page else LIBRARY_NAV_INDEX
        self.nav_buttons.button(nav_index).setChecked(True)

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
