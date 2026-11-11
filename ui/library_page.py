"""Pagina Libreria: filtri a sinistra e griglia delle copertine a destra."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.library import count_by_summary_status, filter_games
from core.models import Game
from core.repository import GameRepository
from ui.game_card import CARD_WIDTH, GameCard

CARD_SPACING = 20
PAGE_MARGIN = 40
SIDEBAR_WIDTH = 220
SCROLLBAR_SPACE = 16
STATUS_FILTERS: list[tuple[str | None, str]] = [
    (None, "Tutti i giochi"),
    ("playing", "In corso"),
    ("completed", "Completati"),
    ("dropped", "Abbandonati"),
    ("backlog", "Backlog"),
]


class LibraryPage(QWidget):
    """Mostra i giochi della libreria come card, filtrabili per stato e titolo."""

    def __init__(self, repository: GameRepository) -> None:
        super().__init__()
        self.repository = repository
        self.games: list[Game] = []
        self.cards: list[GameCard] = []
        self.columns = 0

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Cerca per titolo")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.apply_filters)

        self.status_buttons = QButtonGroup(self)
        sidebar = QFrame()
        sidebar.setObjectName("librarySidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(4)
        sidebar_layout.addWidget(self.search_box)
        sidebar_layout.addSpacing(16)
        for index, (_, label) in enumerate(STATUS_FILTERS):
            button = QPushButton(label)
            button.setObjectName("filterButton")
            button.setCheckable(True)
            self.status_buttons.addButton(button, index)
            sidebar_layout.addWidget(button)
        sidebar_layout.addStretch()
        self.status_buttons.button(0).setChecked(True)
        self.status_buttons.idClicked.connect(self.apply_filters)

        self.heading = QLabel()
        self.heading.setObjectName("pageTitle")

        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(CARD_SPACING)
        self.grid.setVerticalSpacing(28)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.grid_container)

        content = QVBoxLayout()
        content.setSpacing(20)
        content.addWidget(self.heading)
        content.addWidget(self.scroll_area)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, 28, PAGE_MARGIN, 0)
        layout.setSpacing(PAGE_MARGIN)
        layout.addWidget(sidebar)
        layout.addLayout(content)

        self.refresh()

    def refresh(self) -> None:
        """Ricarica i giochi dal repository, aggiorna i conteggi e riapplica i filtri."""
        self.games = self.repository.load_games()
        counts = count_by_summary_status(self.games)
        for index, (status, label) in enumerate(STATUS_FILTERS):
            count = len(self.games) if status is None else counts[status]
            self.status_buttons.button(index).setText(f"{label}   {count}")
        self.apply_filters()

    def apply_filters(self) -> None:
        """Mostra solo i giochi che corrispondono alla ricerca e allo stato scelti."""
        status, label = STATUS_FILTERS[self.status_buttons.checkedId()]
        visible_games = filter_games(self.games, self.search_box.text(), status)
        self.heading.setText(f"{label} · {len(visible_games)}")

        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()
            card.deleteLater()
        self.cards = [GameCard(game) for game in visible_games]
        self.arrange_cards()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Quando la pagina cambia larghezza, ridistribuisce le card se cambia il numero di colonne."""
        super().resizeEvent(event)
        if count_columns(self.available_width()) != self.columns:
            self.arrange_cards()

    def available_width(self) -> int:
        """Restituisce la larghezza utile per le card, tolti margini, filtri e barra di scorrimento."""
        return self.width() - 3 * PAGE_MARGIN - SIDEBAR_WIDTH - SCROLLBAR_SPACE

    def arrange_cards(self) -> None:
        """Dispone le card nella griglia con tante colonne quante ne entrano."""
        self.columns = count_columns(self.available_width())
        for card in self.cards:
            self.grid.removeWidget(card)
        for position, card in enumerate(self.cards):
            row, column = divmod(position, self.columns)
            self.grid.addWidget(card, row, column)


def count_columns(available_width: int) -> int:
    """Restituisce quante card entrano nella larghezza disponibile, almeno una."""
    return max(1, (available_width + CARD_SPACING) // (CARD_WIDTH + CARD_SPACING))