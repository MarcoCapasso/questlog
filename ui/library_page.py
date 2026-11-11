"""Pagina Libreria: ricerca, filtro per stato e griglia delle copertine."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QActionGroup, QResizeEvent
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.library import count_by_summary_status, filter_games
from core.models import Game
from core.repository import GameRepository
from ui.add_game_dialog import AddGameDialog
from ui.game_card import CARD_WIDTH, GameCard

CARD_SPACING = 20
PAGE_MARGIN = 40
SEARCH_WIDTH = 260
SCROLLBAR_SPACE = 16
MENU_GAP = 6
STATUS_FILTERS: list[tuple[str | None, str]] = [
    (None, "Tutti i giochi"),
    ("playing", "In corso"),
    ("completed", "Completati"),
    ("dropped", "Abbandonati"),
    ("backlog", "Da giocare"),
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
        self.search_box.setFixedWidth(SEARCH_WIDTH)
        self.search_box.textChanged.connect(self.apply_filters)

        self.filters_menu = QMenu(self)
        filters_group = QActionGroup(self)
        self.filter_actions: list[QAction] = []
        for _, label in STATUS_FILTERS:
            action = self.filters_menu.addAction(label)
            action.setCheckable(True)
            filters_group.addAction(action)
            self.filter_actions.append(action)
        self.filter_actions[0].setChecked(True)
        filters_group.triggered.connect(self.apply_filters)

        self.filters_button = QPushButton("Filtri")
        self.filters_button.setObjectName("filtersButton")
        self.filters_button.clicked.connect(self.show_filters_menu)

        add_button = QPushButton("Aggiungi gioco")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_game)

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

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        toolbar.addWidget(self.heading)
        toolbar.addStretch()
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(self.filters_button)
        toolbar.addWidget(add_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, 28, PAGE_MARGIN, 0)
        layout.setSpacing(20)
        layout.addLayout(toolbar)
        layout.addWidget(self.scroll_area)

        self.refresh()

    def refresh(self) -> None:
        """Ricarica i giochi dal repository, aggiorna i conteggi e riapplica i filtri."""
        self.games = self.repository.load_games()
        counts = count_by_summary_status(self.games)
        for index, (status, label) in enumerate(STATUS_FILTERS):
            count = len(self.games) if status is None else counts[status]
            self.filter_actions[index].setText(f"{label}\t{count}")
        self.apply_filters()

    def apply_filters(self) -> None:
        """Mostra solo i giochi che corrispondono alla ricerca e allo stato scelti."""
        status, label = STATUS_FILTERS[self.selected_filter_index()]
        visible_games = filter_games(self.games, self.search_box.text(), status)
        self.heading.setText(f"{label} · {len(visible_games)}")
        self.filters_button.setText("Filtri" if status is None else f"Filtri · {label}")

        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()
            card.deleteLater()
        self.cards = [GameCard(game) for game in visible_games]
        self.arrange_cards()

    def add_game(self) -> None:
        """Apre il form di aggiunta e, se l'utente salva, aggiunge il gioco alla libreria."""
        dialog = AddGameDialog(self.games, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.repository.save_games(self.games + [dialog.created_game()])
            self.refresh()


    def show_filters_menu(self) -> None:
        """Apre il menu dei filtri sotto il bottone, allineato al suo bordo destro."""
        button = self.filters_button
        menu_width = self.filters_menu.sizeHint().width()
        position = button.mapToGlobal(QPoint(button.width() - menu_width, button.height() + MENU_GAP))
        self.filters_menu.popup(position)

    def selected_filter_index(self) -> int:
        """Restituisce la posizione in STATUS_FILTERS del filtro scelto nel menu."""
        for index, action in enumerate(self.filter_actions):
            if action.isChecked():
                return index
        return 0

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