"""Griglia di card che si adatta alla larghezza: la usano la libreria e il catalogo."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QWidget

from ui.game_card import CARD_WIDTH, ClickableCard

CARD_SPACING = 20
ROW_SPACING = 28


class CardGrid(QWidget):
    """Dispone le card su più colonne; con max_rows mostra solo le prime righe (per esempio una sola)."""

    def __init__(self, max_rows: int | None = None) -> None:
        super().__init__()
        self.max_rows = max_rows
        self.cards: list[ClickableCard] = []
        self.columns = 1
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(CARD_SPACING)
        self.grid.setVerticalSpacing(ROW_SPACING)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def set_cards(self, cards: list[ClickableCard]) -> None:
        """Sostituisce le card mostrate con quelle nuove."""
        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()
            card.deleteLater()
        self.cards = cards
        self.arrange()

    def set_columns(self, columns: int) -> None:
        """Cambia il numero di colonne e ridispone le card, solo se è davvero cambiato."""
        if columns != self.columns:
            self.columns = columns
            self.arrange()

    def arrange(self) -> None:
        """Dispone le card riga per riga, nascondendo quelle oltre max_rows."""
        for card in self.cards:
            self.grid.removeWidget(card)
        for position, card in enumerate(self.cards):
            row, column = divmod(position, self.columns)
            if self.max_rows is not None and row >= self.max_rows:
                card.hide()
                continue
            self.grid.addWidget(card, row, column)
            card.show()


def count_columns(available_width: int) -> int:
    """Restituisce quante card entrano nella larghezza disponibile, almeno una."""
    return max(1, (available_width + CARD_SPACING) // (CARD_WIDTH + CARD_SPACING))
