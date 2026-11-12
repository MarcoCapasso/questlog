"""Pagina Libreria: ricerca, filtro per stato e griglia delle copertine."""

from collections.abc import Callable

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QResizeEvent
from PySide6.QtWidgets import (
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
from ui.card_grid import CardGrid, count_columns
from ui.game_card import ClickableCard, GameCard

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

    add_requested = Signal()
    game_selected = Signal(Game)

    def __init__(self, repository: GameRepository) -> None:
        super().__init__()
        self.repository = repository
        self.games: list[Game] = []

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
        add_button.clicked.connect(self.add_requested.emit)

        self.heading = QLabel()
        self.heading.setObjectName("pageTitle")

        self.card_grid = CardGrid()
        self.empty_state = create_empty_state(self.add_requested.emit)
        self.no_results = QLabel("Nessun gioco corrisponde alla ricerca o al filtro.")
        self.no_results.setObjectName("sectionMessage")
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, PAGE_MARGIN)
        scroll_layout.addWidget(self.empty_state)
        scroll_layout.addWidget(self.no_results)
        scroll_layout.addWidget(self.card_grid)
        scroll_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(scroll_content)

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
        library_empty = not self.games
        self.empty_state.setVisible(library_empty)
        self.no_results.setVisible(not library_empty and not visible_games)
        for widget in (self.search_box, self.filters_button):
            widget.setVisible(not library_empty)
        self.filters_button.setText("Filtri" if status is None else f"Filtri · {label}")

        cards: list[ClickableCard] = []
        for game in visible_games:
            card = GameCard(game)
            card.clicked.connect(lambda chosen=game: self.game_selected.emit(chosen))
            cards.append(card)
        self.card_grid.set_cards(cards)

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
        """Quando la pagina cambia larghezza, adatta il numero di colonne della griglia."""
        super().resizeEvent(event)
        self.card_grid.set_columns(count_columns(self.width() - 2 * PAGE_MARGIN - SCROLLBAR_SPACE))


def create_empty_state(on_add: Callable[[], None]) -> QWidget:
    """Restituisce l'invito mostrato quando la libreria è vuota, con il bottone che apre il catalogo."""
    title = QLabel("La tua libreria è vuota")
    title.setObjectName("sectionTitle")
    text = QLabel("Cerca un gioco nel catalogo IGDB e aggiungilo: lo ritroverai qui, con le tue partite.")
    text.setObjectName("sectionMessage")
    button = QPushButton("Aggiungi il primo gioco")
    button.setObjectName("primaryButton")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.clicked.connect(on_add)

    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 48, 0, 0)
    layout.setSpacing(12)
    layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)
    layout.addWidget(text, alignment=Qt.AlignmentFlag.AlignHCenter)
    layout.addSpacing(8)
    layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)
    return panel
