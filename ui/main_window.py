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
from ui.catalog_page import CatalogPage
from ui.game_page import GamePage
from ui.library_page import LibraryPage

LIBRARY_NAV_INDEX = 1


class MainWindow(QMainWindow):
    """La finestra principale: barra di navigazione in alto e, sotto, una pagina alla volta."""

    def __init__(self, repository: GameRepository, catalog: GameCatalog) -> None:
        super().__init__()
        self.setWindowTitle("Questlog")
        screen_area = self.screen().availableGeometry()
        self.resize(int(screen_area.width() * 0.7), int(screen_area.height() * 0.75))
        self.setMinimumSize(960, 600)

        self.library_page = LibraryPage(repository)
        self.catalog_page = CatalogPage(catalog, repository)
        self.game_page = GamePage(repository, catalog)
        self.page_before_game: QWidget = self.library_page

        self.library_page.add_requested.connect(self.show_catalog_page)
        self.library_page.game_selected.connect(self.show_library_game)
        self.catalog_page.back_requested.connect(self.show_library_page)
        self.catalog_page.game_selected.connect(self.show_catalog_game)
        self.game_page.back_requested.connect(self.go_back_from_game)
        self.game_page.library_changed.connect(self.library_page.refresh)

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
            ("Home", create_placeholder_page("Home")),
            ("Libreria", self.library_page),
            ("Statistiche", create_placeholder_page("Statistiche")),
        ]
        for index, (name, page) in enumerate(pages):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setCheckable(True)
            self.nav_buttons.addButton(button, index)
            header_layout.addWidget(button)
            self.pages.addWidget(page)
        header_layout.addStretch()
        self.pages.addWidget(self.catalog_page)
        self.pages.addWidget(self.game_page)

        self.nav_buttons.idClicked.connect(self.pages.setCurrentIndex)
        self.nav_buttons.button(0).setChecked(True)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(header)
        central_layout.addWidget(self.pages)
        self.setCentralWidget(central)

    def show_page(self, page: QWidget) -> None:
        """Mostra una pagina; quelle senza bottone in alto (catalogo e gioco) tengono evidenziato 'Libreria'."""
        self.pages.setCurrentWidget(page)
        self.nav_buttons.button(LIBRARY_NAV_INDEX).setChecked(True)

    def show_library_page(self) -> None:
        """Torna alla libreria."""
        self.show_page(self.library_page)

    def show_catalog_page(self) -> None:
        """Apre il catalogo per scegliere un gioco da aggiungere."""
        self.catalog_page.start()
        self.show_page(self.catalog_page)

    def show_catalog_game(self, catalog_game: CatalogGame) -> None:
        """Apre la pagina di un gioco scelto nel catalogo."""
        self.page_before_game = self.catalog_page
        self.game_page.show_catalog_game(catalog_game)
        self.show_page(self.game_page)

    def show_library_game(self, game: Game) -> None:
        """Apre la pagina di un gioco cliccato in libreria."""
        self.page_before_game = self.library_page
        self.game_page.show_library_game(game)
        self.show_page(self.game_page)

    def go_back_from_game(self) -> None:
        """Torna alla pagina da cui si era aperto il gioco, aggiornandola."""
        if self.page_before_game is self.catalog_page:
            self.catalog_page.refresh_cards()
        self.show_page(self.page_before_game)


def create_placeholder_page(title: str) -> QWidget:
    """Restituisce una pagina provvisoria che mostra solo il proprio titolo."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(40, 28, 40, 28)
    layout.addWidget(QLabel(title))
    layout.addStretch()
    return page
