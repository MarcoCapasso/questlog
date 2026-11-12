"""Pagina Home: il gioco in corso in primo piano, i numeri della libreria e i giochi giocati di recente."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from core.analysis import summarize_library
from core.catalog import CatalogGame, GameCatalog
from core.library import current_playthrough, recently_played
from core.models import Game
from core.repository import GameRepository
from ui.backdrop import BackdropWidget
from ui.card_grid import CardGrid, count_columns
from ui.covers import CoverLabel
from ui.formatting import format_summary
from ui.game_card import ClickableCard, GameCard
from ui.game_page import format_date
from ui.tasks import run_in_background

PAGE_MARGIN = 40
SCROLLBAR_SPACE = 16
HERO_COVER_SIZE = QSize(150, 200)
RECENT_LIMIT = 12


class HomePage(QWidget):
    """Home di Questlog; emette segnali e lascia alla finestra principale la navigazione."""

    game_selected = Signal(Game)
    update_requested = Signal(Game, int)
    library_requested = Signal()
    add_requested = Signal()

    def __init__(self, repository: GameRepository, catalog: GameCatalog) -> None:
        super().__init__()
        self.repository = repository
        self.catalog = catalog
        self.current: tuple[Game, int] | None = None

        self.cover_holder = QVBoxLayout()
        self.cover_holder.setContentsMargins(0, 0, 0, 0)
        self.eyebrow = QLabel("Stai giocando")
        self.eyebrow.setObjectName("heroEyebrow")
        self.hero_title = QLabel()
        self.hero_title.setObjectName("gameTitle")
        self.hero_title.setWordWrap(True)
        self.hero_details = QLabel()
        self.hero_details.setObjectName("gameMeta")
        self.hero_details.setWordWrap(True)

        self.update_button = QPushButton("Aggiorna la partita")
        self.update_button.setObjectName("accentButton")
        self.update_button.clicked.connect(self.request_update)
        self.open_button = QPushButton("Apri scheda")
        self.open_button.clicked.connect(self.open_current_game)
        self.library_button = QPushButton("Vai alla libreria")
        self.library_button.setObjectName("primaryButton")
        self.library_button.clicked.connect(self.library_requested.emit)
        self.add_button = QPushButton("Aggiungi il primo gioco")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_requested.emit)
        hero_actions = QHBoxLayout()
        hero_actions.setSpacing(10)
        hero_actions.addWidget(self.update_button)
        hero_actions.addWidget(self.open_button)
        hero_actions.addWidget(self.library_button)
        hero_actions.addWidget(self.add_button)
        hero_actions.addStretch()

        hero_text = QVBoxLayout()
        hero_text.setSpacing(10)
        hero_text.addStretch()
        hero_text.addWidget(self.eyebrow)
        hero_text.addWidget(self.hero_title)
        hero_text.addWidget(self.hero_details)
        hero_text.addSpacing(8)
        hero_text.addLayout(hero_actions)

        hero = QHBoxLayout()
        hero.setSpacing(32)
        hero.addLayout(self.cover_holder)
        hero.addLayout(hero_text, stretch=1)

        self.stats_label = QLabel()
        self.stats_label.setObjectName("statsLine")
        self.stats_label.setTextFormat(Qt.TextFormat.RichText)
        self.stats_label.setWordWrap(True)

        recent_title = QLabel("Giocati di recente")
        recent_title.setObjectName("sectionTitle")
        all_games_button = QPushButton("Tutta la libreria")
        all_games_button.setObjectName("textButton")
        all_games_button.setCursor(Qt.CursorShape.PointingHandCursor)
        all_games_button.clicked.connect(self.library_requested.emit)
        recent_heading = QHBoxLayout()
        recent_heading.addWidget(recent_title)
        recent_heading.addStretch()
        recent_heading.addWidget(all_games_button)
        self.recent_message = QLabel("Quando registri una partita con le date, la trovi qui.")
        self.recent_message.setObjectName("sectionMessage")
        self.recent_grid = CardGrid(max_rows=1)
        self.recent_section = QWidget()
        recent_layout = QVBoxLayout(self.recent_section)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(28)
        recent_layout.addLayout(recent_heading)
        recent_layout.addWidget(self.recent_message)
        recent_layout.addWidget(self.recent_grid)

        self.backdrop = BackdropWidget()
        content = QVBoxLayout(self.backdrop)
        content.setContentsMargins(PAGE_MARGIN, 48, PAGE_MARGIN, PAGE_MARGIN)
        content.setSpacing(28)
        content.addLayout(hero)
        content.addWidget(self.stats_label)
        content.addSpacing(8)
        content.addWidget(self.recent_section)
        content.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.backdrop)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)

    def refresh(self) -> None:
        """Rilegge la libreria e aggiorna tutta la pagina."""
        games = self.repository.load_games()
        self.current = current_playthrough(games)
        self.show_current_game(library_empty=not games)
        self.recent_section.setVisible(bool(games))
        self.stats_label.setText(format_summary(summarize_library(games)))
        self.stats_label.setVisible(any(game.playthroughs for game in games))
        self.show_recent_games(recently_played(games, RECENT_LIMIT))

    def show_current_game(self, library_empty: bool) -> None:
        """Mostra in primo piano la partita in corso, oppure un invito a iniziarne una (o ad aggiungere giochi)."""
        playing = self.current is not None
        self.eyebrow.setVisible(playing)
        self.update_button.setVisible(playing)
        self.open_button.setVisible(playing)
        self.library_button.setVisible(not playing and not library_empty)
        self.add_button.setVisible(library_empty)
        self.backdrop.set_url(None)
        if library_empty:
            self.replace_cover(None, visible=False)
            self.hero_title.setText("Benvenuto su Questlog")
            self.hero_details.setText(
                "La tua libreria è ancora vuota. Cerca i giochi che stai giocando o che hai finito "
                "e aggiungili: qui troverai la partita in corso e i giochi recenti."
            )
            return
        if self.current is None:
            self.replace_cover(None, visible=False)
            self.hero_title.setText("Nessun gioco in corso")
            self.hero_details.setText("Apri un gioco della tua libreria e registra una nuova partita.")
            return

        game, index = self.current
        playthrough = game.playthroughs[index]
        self.replace_cover(game.cover_url)
        self.hero_title.setText(game.title)
        details = f"{playthrough.hours_played:g} ore su {playthrough.platform}"
        if playthrough.start_date is not None:
            details += f" · partita iniziata il {format_date(playthrough.start_date)}"
        self.hero_details.setText(details)
        if game.igdb_id is not None:
            igdb_id = game.igdb_id
            run_in_background(lambda: self.catalog.details(igdb_id), self.on_details_loaded, self.ignore_error)

    def on_details_loaded(self, details: CatalogGame | None) -> None:
        """Usa l'immagine di IGDB come sfondo, se riguarda ancora il gioco in primo piano."""
        if details is None or self.current is None or self.current[0].igdb_id != details.igdb_id:
            return
        self.backdrop.set_url(details.backdrop_url)

    def ignore_error(self, _message: str) -> None:
        """Senza internet la Home funziona lo stesso, solo senza sfondo."""

    def replace_cover(self, cover_url: str | None, visible: bool = True) -> None:
        """Sostituisce la copertina del gioco in primo piano; senza gioco in corso la nasconde."""
        while self.cover_holder.count():
            item = self.cover_holder.takeAt(0)
            old_cover = item.widget() if item is not None else None
            if old_cover is not None:
                old_cover.deleteLater()
        cover = CoverLabel(cover_url, HERO_COVER_SIZE)
        cover.setVisible(visible)
        self.cover_holder.addWidget(cover)

    def show_recent_games(self, games: list[Game]) -> None:
        """Mostra una riga di card dei giochi giocati di recente."""
        cards: list[ClickableCard] = []
        for game in games:
            card = GameCard(game)
            card.clicked.connect(lambda chosen=game: self.game_selected.emit(chosen))
            cards.append(card)
        self.recent_grid.set_cards(cards)
        self.recent_message.setVisible(not games)

    def request_update(self) -> None:
        """Chiede di aprire il gioco in corso con la sua partita pronta da modificare."""
        if self.current is not None:
            game, index = self.current
            self.update_requested.emit(game, index)

    def open_current_game(self) -> None:
        """Chiede di aprire la scheda del gioco in corso."""
        if self.current is not None:
            self.game_selected.emit(self.current[0])

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Adatta il numero di card dei giochi recenti alla larghezza."""
        super().resizeEvent(event)
        self.recent_grid.set_columns(count_columns(self.width() - 2 * PAGE_MARGIN - SCROLLBAR_SPACE))
