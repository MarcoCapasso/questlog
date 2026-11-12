"""Pagina Aggiungi gioco: ricerca nel catalogo IGDB e sezioni con i giochi del momento."""

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent, QResizeEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.catalog import CatalogGame, GameCatalog, find_library_game
from core.models import Game
from core.repository import GameRepository
from ui.card_grid import CardGrid, count_columns
from ui.game_card import CatalogCard, ClickableCard
from ui.tasks import run_in_background

PAGE_MARGIN = 40
SCROLLBAR_SPACE = 16
SEARCH_WIDTH = 520
SEARCH_DELAY_MS = 400


class CatalogSection(QWidget):
    """Un titolo e una griglia di giochi che arrivano dal catalogo, con i messaggi di caricamento ed errore."""

    def __init__(
        self,
        title: str,
        create_cards: Callable[[list[CatalogGame]], list[ClickableCard]],
        max_rows: int | None = None,
    ) -> None:
        super().__init__()
        self.create_cards = create_cards
        self.load_games: Callable[[], list[CatalogGame]] | None = None
        self.games: list[CatalogGame] = []
        self.request_id = 0

        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.message_label = QLabel()
        self.message_label.setObjectName("sectionMessage")
        self.message_label.setWordWrap(True)
        self.retry_button = QPushButton("Riprova")
        self.retry_button.clicked.connect(self.reload)
        self.grid = CardGrid(max_rows)

        message_row = QHBoxLayout()
        message_row.setSpacing(12)
        message_row.addWidget(self.message_label)
        message_row.addWidget(self.retry_button)
        message_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self.title_label)
        layout.addLayout(message_row)
        layout.addWidget(self.grid)

    def set_title(self, title: str) -> None:
        """Cambia il titolo della sezione."""
        self.title_label.setText(title)

    def load(self, load_games: Callable[[], list[CatalogGame]]) -> None:
        """Chiede i giochi al catalogo in background e intanto mostra 'Caricamento…'."""
        self.load_games = load_games
        self.request_id += 1
        request_id = self.request_id
        self.show_message("Caricamento…")
        self.grid.set_cards([])
        run_in_background(lambda: (request_id, load_games()), self.on_loaded, self.on_failed)

    def reload(self) -> None:
        """Ripete l'ultima richiesta, per esempio dopo un errore di rete."""
        if self.load_games is not None:
            self.load(self.load_games)

    def on_loaded(self, result: tuple[int, list[CatalogGame]]) -> None:
        """Mostra i giochi arrivati, ignorando le risposte di richieste ormai superate."""
        request_id, games = result
        if request_id != self.request_id:
            return
        self.games = games
        self.refresh_cards()

    def on_failed(self, message: str) -> None:
        """Mostra l'errore e il bottone Riprova."""
        self.show_message(message, can_retry=True)

    def refresh_cards(self) -> None:
        """Ricrea le card, per esempio quando un gioco entra in libreria."""
        if self.load_games is None:
            return
        if not self.games:
            self.show_message("Nessun gioco trovato.")
        else:
            self.message_label.hide()
            self.retry_button.hide()
        self.grid.set_cards(self.create_cards(self.games))

    def show_message(self, text: str, can_retry: bool = False) -> None:
        """Mostra un messaggio al posto della griglia."""
        self.message_label.setText(text)
        self.message_label.show()
        self.retry_button.setVisible(can_retry)


class CatalogPage(QWidget):
    """Barra di ricerca e, sotto, le sezioni del catalogo oppure i risultati della ricerca."""

    game_selected = Signal(object)
    back_requested = Signal()

    def __init__(self, catalog: GameCatalog, repository: GameRepository) -> None:
        super().__init__()
        self.catalog = catalog
        self.repository = repository
        self.library_games: list[Game] = []
        self.sections_loaded = False

        self.back_button = QPushButton()
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back_requested.emit)

        self.heading = QLabel()
        self.heading.setObjectName("pageTitle")
        self.link_hint = QLabel()
        self.link_hint.setObjectName("gameMeta")
        self.link_hint.setWordWrap(True)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("catalogSearch")
        self.search_box.setPlaceholderText("Cerca un gioco nel catalogo")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setMaximumWidth(SEARCH_WIDTH)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(SEARCH_DELAY_MS)
        self.search_timer.timeout.connect(self.run_search)
        self.search_box.textChanged.connect(self.search_timer.start)
        self.search_box.returnPressed.connect(self.run_search)

        demo_notice = QLabel(
            "Catalogo di prova: IGDB non è ancora configurato, quindi vedi solo alcuni giochi di esempio."
        )
        demo_notice.setObjectName("demoNotice")
        demo_notice.setWordWrap(True)
        demo_notice.setVisible(catalog.is_demo)

        self.sections = [
            (CatalogSection("Di tendenza", self.create_cards, max_rows=1), catalog.trending),
            (CatalogSection("Nuove uscite", self.create_cards, max_rows=1), catalog.new_releases),
            (CatalogSection("In arrivo", self.create_cards, max_rows=1), catalog.upcoming),
        ]
        self.results = CatalogSection("Risultati", self.create_cards)
        self.results.hide()

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, PAGE_MARGIN)
        scroll_layout.setSpacing(36)
        for section, _ in self.sections:
            scroll_layout.addWidget(section)
        scroll_layout.addWidget(self.results)
        scroll_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, 20, PAGE_MARGIN, 0)
        layout.setSpacing(12)
        layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.heading)
        layout.addWidget(self.link_hint)
        layout.addWidget(self.search_box)
        layout.addWidget(demo_notice)
        layout.addSpacing(12)
        layout.addWidget(scroll_area)

    def start(self, link_title: str | None = None) -> None:
        """Prepara la pagina quando viene aperta: legge la libreria e, la prima volta, carica le sezioni.

        Con link_title la pagina serve a collegare a IGDB un gioco già in libreria:
        cambia titolo e testo del bottone indietro, e cerca subito quel titolo.
        """
        self.library_games = self.repository.load_games()
        if not self.sections_loaded:
            self.sections_loaded = True
            for section, load_games in self.sections:
                section.load(load_games)
        else:
            self.refresh_cards()

        linking = link_title is not None
        self.heading.setText("Collega a IGDB" if linking else "Aggiungi gioco")
        self.back_button.setText("← Indietro" if linking else "← Libreria")
        self.link_hint.setText(
            f"Scegli il gioco che corrisponde a «{link_title}»: arriveranno copertina, descrizione e "
            "screenshot, mentre le tue partite e il voto restano come sono."
        )
        self.link_hint.setVisible(linking)
        self.search_box.setText(link_title or "")
        self.run_search()
        self.search_box.setFocus()

    def refresh_cards(self) -> None:
        """Aggiorna tutte le card, per esempio il segno 'In libreria' dopo un'aggiunta."""
        self.library_games = self.repository.load_games()
        for section, _ in self.sections:
            section.refresh_cards()
        self.results.refresh_cards()

    def create_cards(self, games: list[CatalogGame]) -> list[ClickableCard]:
        """Crea una card cliccabile per ogni gioco, segnando quelli già in libreria."""
        cards: list[ClickableCard] = []
        for catalog_game in games:
            in_library = find_library_game(self.library_games, catalog_game) is not None
            card = CatalogCard(catalog_game, in_library)
            card.clicked.connect(lambda chosen=catalog_game: self.game_selected.emit(chosen))
            cards.append(card)
        return cards

    def run_search(self) -> None:
        """Cerca il testo scritto; con la barra vuota torna alle sezioni del catalogo."""
        self.search_timer.stop()
        text = self.search_box.text().strip()
        searching = text != ""
        for section, _ in self.sections:
            section.setVisible(not searching)
        self.results.setVisible(searching)
        if searching:
            self.results.set_title(f"Risultati per “{text}”")
            self.results.load(lambda: self.catalog.search(text))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Con Esc svuota la ricerca, oppure torna alla libreria se è già vuota."""
        if event.key() == Qt.Key.Key_Escape:
            if self.search_box.text():
                self.search_box.clear()
            else:
                self.back_requested.emit()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Quando la pagina cambia larghezza, adatta il numero di colonne di tutte le griglie."""
        super().resizeEvent(event)
        columns = count_columns(self.width() - 2 * PAGE_MARGIN - SCROLLBAR_SPACE)
        for section, _ in self.sections:
            section.grid.set_columns(columns)
        self.results.grid.set_columns(columns)
