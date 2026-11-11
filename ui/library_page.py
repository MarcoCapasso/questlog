"""Pagina Libreria: la griglia delle copertine di tutti i giochi."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from core.repository import GameRepository
from ui.game_card import GameCard

COLUMNS = 5


class LibraryPage(QWidget):
    """Mostra tutti i giochi della libreria come card in griglia."""

    def __init__(self, repository: GameRepository) -> None:
        super().__init__()
        self.repository = repository

        self.heading = QLabel()
        self.heading.setObjectName("pageTitle")

        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setHorizontalSpacing(20)
        self.grid.setVerticalSpacing(28)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.grid_container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 28, 40, 0)
        layout.setSpacing(20)
        layout.addWidget(self.heading)
        layout.addWidget(scroll_area)

        self.refresh()

    def refresh(self) -> None:
        """Ricarica i giochi dal repository e ricostruisce la griglia."""
        games = self.repository.load_games()
        self.heading.setText(f"Libreria · {len(games)} giochi")
        for position, game in enumerate(games):
            row, column = divmod(position, COLUMNS)
            self.grid.addWidget(GameCard(game), row, column)