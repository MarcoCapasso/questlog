"""Pagina Libreria: la griglia delle copertine di tutti i giochi."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from core.repository import GameRepository
from ui.game_card import CARD_WIDTH, GameCard

CARD_SPACING = 20
PAGE_MARGIN = 40
SCROLLBAR_SPACE = 16


class LibraryPage(QWidget):
    """Mostra tutti i giochi della libreria come card in una griglia che si adatta alla larghezza."""

    def __init__(self, repository: GameRepository) -> None:
        super().__init__()
        self.repository = repository
        self.cards: list[GameCard] = []
        self.columns = 0

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, 28, PAGE_MARGIN, 0)
        layout.setSpacing(20)
        layout.addWidget(self.heading)
        layout.addWidget(self.scroll_area)

        self.refresh()

    def refresh(self) -> None:
        """Ricarica i giochi dal repository e ricrea le card."""
        for card in self.cards:
            self.grid.removeWidget(card)
            card.deleteLater()
        games = self.repository.load_games()
        self.cards = [GameCard(game) for game in games]
        self.heading.setText(f"Libreria · {len(games)} giochi")
        self.arrange_cards()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Quando la pagina cambia larghezza, ridistribuisce le card se cambia il numero di colonne."""
        super().resizeEvent(event)
        if count_columns(self.available_width()) != self.columns:
            self.arrange_cards()

    def available_width(self) -> int:
        """Restituisce la larghezza utile per le card, tolti i margini e la barra di scorrimento."""
        return self.width() - 2 * PAGE_MARGIN - SCROLLBAR_SPACE

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