"""Pagina di un gioco: dati dal catalogo IGDB, aggiunta alla libreria, voto e partite."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.catalog import CatalogGame, GameCatalog, find_library_game, game_from_catalog, link_to_catalog
from core.library import calculate_total_hours, find_game_index_by_title, find_platform_spelling, known_platforms
from core.models import Game, Playthrough
from core.repository import GameRepository
from ui.covers import CoverLabel
from ui.game_card import PLAYTHROUGH_STATUS_LABELS, format_release_year
from ui.playthrough_form import PlaythroughForm
from ui.tasks import run_in_background
from ui.widgets import RatingInput

PAGE_MARGIN = 40
COVER_SIZE = QSize(210, 280)
SUMMARY_WIDTH = 680
NOT_LINKED_HINT = "Cercalo in Aggiungi gioco per collegarlo a IGDB e vedere copertina e descrizione."


class GamePage(QWidget):
    """Mostra un gioco del catalogo o della libreria; se è in libreria permette di votarlo e registrare partite."""

    back_requested = Signal()
    library_changed = Signal()

    def __init__(self, repository: GameRepository, catalog: GameCatalog) -> None:
        super().__init__()
        self.repository = repository
        self.catalog = catalog
        self.games: list[Game] = []
        self.platform_suggestions: list[str] = []
        self.game: Game | None = None
        self.catalog_game: CatalogGame | None = None

        back_button = QPushButton("← Indietro")
        back_button.setObjectName("backButton")
        back_button.clicked.connect(self.back_requested.emit)

        self.cover_holder = QVBoxLayout()
        self.cover_holder.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel()
        self.title_label.setObjectName("gameTitle")
        self.title_label.setWordWrap(True)
        self.meta_label = QLabel()
        self.meta_label.setObjectName("gameMeta")
        self.meta_label.setWordWrap(True)
        self.platforms_label = QLabel()
        self.platforms_label.setObjectName("gameMeta")
        self.platforms_label.setWordWrap(True)
        self.summary_label = QLabel()
        self.summary_label.setObjectName("gameSummary")
        self.summary_label.setWordWrap(True)
        self.summary_label.setMaximumWidth(SUMMARY_WIDTH)

        self.add_button = QPushButton("Aggiungi alla libreria")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_to_library)
        self.in_library_chip = QLabel("Nella tua libreria")
        self.in_library_chip.setObjectName("libraryChip")
        actions = QHBoxLayout()
        actions.addWidget(self.add_button)
        actions.addWidget(self.in_library_chip)
        actions.addStretch()

        info = QVBoxLayout()
        info.setSpacing(10)
        info.addStretch()
        info.addWidget(self.title_label)
        info.addWidget(self.meta_label)
        info.addWidget(self.platforms_label)
        info.addSpacing(6)
        info.addLayout(actions)

        hero = QHBoxLayout()
        hero.setSpacing(32)
        hero.addLayout(self.cover_holder)
        hero.addLayout(info, stretch=1)

        self.rating_input = RatingInput()
        self.rating_input.rating_changed.connect(self.change_rating)
        self.total_hours_label = QLabel()
        self.total_hours_label.setObjectName("gameMeta")

        self.new_playthrough_button = QPushButton("Nuova partita")
        self.new_playthrough_button.clicked.connect(self.open_playthrough_form)
        playthroughs_heading = QHBoxLayout()
        playthroughs_heading.addWidget(create_section_title("Partite"))
        playthroughs_heading.addStretch()
        playthroughs_heading.addWidget(self.new_playthrough_button)

        self.playthrough_form = PlaythroughForm()
        self.playthrough_form.setMaximumWidth(SUMMARY_WIDTH)
        self.playthrough_form.submitted.connect(self.add_playthrough)
        self.playthrough_form.cancelled.connect(self.playthrough_form.hide)
        self.playthrough_list = QVBoxLayout()
        self.playthrough_list.setSpacing(10)

        self.library_section = QWidget()
        self.library_section.setMaximumWidth(SUMMARY_WIDTH)
        library_layout = QVBoxLayout(self.library_section)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(14)
        library_layout.addWidget(create_section_title("Il tuo voto"))
        library_layout.addWidget(self.rating_input)
        library_layout.addSpacing(18)
        library_layout.addLayout(playthroughs_heading)
        library_layout.addWidget(self.total_hours_label)
        library_layout.addWidget(self.playthrough_form)
        library_layout.addLayout(self.playthrough_list)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, PAGE_MARGIN)
        content_layout.setSpacing(28)
        content_layout.addLayout(hero)
        content_layout.addWidget(self.summary_label)
        content_layout.addWidget(self.library_section)
        content_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, 20, PAGE_MARGIN, 0)
        layout.setSpacing(16)
        layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(scroll_area)

    def show_catalog_game(self, catalog_game: CatalogGame) -> None:
        """Mostra un gioco scelto nel catalogo; se era già in libreria con lo stesso titolo, lo collega a IGDB."""
        self.games = self.repository.load_games()
        self.catalog_game = catalog_game
        self.game = find_library_game(self.games, catalog_game)
        if self.game is not None and self.game.igdb_id is None:
            link_to_catalog(self.game, catalog_game)
            self.save()
        self.update_view()

    def show_library_game(self, game: Game) -> None:
        """Mostra un gioco della libreria e, se è collegato a IGDB, ne scarica la descrizione."""
        self.games = self.repository.load_games()
        index = find_game_index_by_title(self.games, game.title)
        self.game = self.games[index] if index is not None else game
        self.catalog_game = None
        self.update_view()
        if self.game.igdb_id is not None:
            igdb_id = self.game.igdb_id
            run_in_background(lambda: self.catalog.details(igdb_id), self.on_details_loaded, self.ignore_error)

    def on_details_loaded(self, catalog_game: CatalogGame | None) -> None:
        """Completa la pagina con i dati di IGDB, se riguardano ancora il gioco mostrato."""
        if catalog_game is None or self.game is None or self.game.igdb_id != catalog_game.igdb_id:
            return
        self.catalog_game = catalog_game
        self.update_view()

    def ignore_error(self, _message: str) -> None:
        """Senza internet la pagina resta valida, solo senza descrizione: l'errore si può ignorare."""

    def update_view(self) -> None:
        """Aggiorna tutta la pagina con i dati del gioco attuale."""
        catalog_game = self.catalog_game
        title = ""
        cover_url = None
        if catalog_game is not None:
            title, cover_url = catalog_game.title, catalog_game.cover_url
        elif self.game is not None:
            title, cover_url = self.game.title, self.game.cover_url

        self.replace_cover(cover_url)
        self.title_label.setText(title)
        if catalog_game is not None:
            self.meta_label.setText(format_meta(catalog_game))
        else:
            self.meta_label.setText(NOT_LINKED_HINT)
        self.meta_label.setVisible(catalog_game is not None or (self.game is not None and self.game.igdb_id is None))
        platforms = " · ".join(catalog_game.platforms) if catalog_game is not None else ""
        self.platforms_label.setText(platforms)
        self.platforms_label.setVisible(platforms != "")
        summary = catalog_game.summary if catalog_game is not None else ""
        self.summary_label.setText(summary)
        self.summary_label.setVisible(summary != "")

        in_library = self.game is not None
        self.add_button.setVisible(not in_library)
        self.in_library_chip.setVisible(in_library)
        self.library_section.setVisible(in_library)
        self.playthrough_form.hide()
        if self.game is not None:
            self.rating_input.set_rating(None if self.game.rating is None else int(self.game.rating))
            self.render_playthroughs(self.game)

    def replace_cover(self, cover_url: str | None) -> None:
        """Sostituisce il riquadro della copertina con quello della nuova immagine."""
        while self.cover_holder.count():
            item = self.cover_holder.takeAt(0)
            old_cover = item.widget() if item is not None else None
            if old_cover is not None:
                old_cover.deleteLater()
        self.cover_holder.addWidget(CoverLabel(cover_url, COVER_SIZE))

    def render_playthroughs(self, game: Game) -> None:
        """Ricrea l'elenco delle partite, dalla più recente, con il totale delle ore."""
        while self.playthrough_list.count():
            item = self.playthrough_list.takeAt(0)
            old_row = item.widget() if item is not None else None
            if old_row is not None:
                old_row.deleteLater()
        if not game.playthroughs:
            self.total_hours_label.setText("Non l'hai ancora iniziato.")
            return
        self.total_hours_label.setText(f"{calculate_total_hours(game):g} ore in totale")
        for playthrough in reversed(game.playthroughs):
            self.playthrough_list.addWidget(PlaythroughRow(playthrough))

    def add_to_library(self) -> None:
        """Aggiunge alla libreria il gioco del catalogo mostrato, come gioco da giocare."""
        if self.catalog_game is None:
            return
        self.game = game_from_catalog(self.catalog_game)
        self.games.append(self.game)
        self.save()
        self.update_view()

    def change_rating(self, rating: int | None) -> None:
        """Salva subito il voto scelto con le stelle."""
        if self.game is None:
            return
        self.game.rating = rating
        self.save()

    def open_playthrough_form(self) -> None:
        """Apre il form della nuova partita, proponendo prima le piattaforme del gioco e poi quelle già usate."""
        suggestions = list(self.catalog_game.platforms) if self.catalog_game is not None else []
        for platform in known_platforms(self.games):
            if platform not in suggestions:
                suggestions.append(platform)
        self.platform_suggestions = suggestions
        self.playthrough_form.start(suggestions)
        self.playthrough_form.show()

    def add_playthrough(self, playthrough: Playthrough) -> None:
        """Aggiunge la partita al gioco, usando la grafia già presente tra i suggerimenti o in libreria."""
        if self.game is None:
            return
        playthrough.platform = find_platform_spelling(self.games, playthrough.platform)
        for suggestion in self.platform_suggestions:
            if suggestion.lower() == playthrough.platform.lower():
                playthrough.platform = suggestion
        self.game.playthroughs.append(playthrough)
        self.save()
        self.update_view()

    def save(self) -> None:
        """Salva la libreria e avvisa la finestra che è cambiata."""
        self.repository.save_games(self.games)
        self.library_changed.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Con Esc chiude il form della partita, oppure torna indietro."""
        if event.key() == Qt.Key.Key_Escape:
            if self.playthrough_form.isVisible():
                self.playthrough_form.hide()
            else:
                self.back_requested.emit()
            return
        super().keyPressEvent(event)


class PlaythroughRow(QFrame):
    """Una riga dell'elenco partite: piattaforma e stato, date, ore."""

    def __init__(self, playthrough: Playthrough) -> None:
        super().__init__()
        self.setObjectName("playthroughRow")
        self.setMaximumWidth(SUMMARY_WIDTH)

        title = QLabel(f"{playthrough.platform} · {PLAYTHROUGH_STATUS_LABELS[playthrough.status]}")
        title.setObjectName("cardTitle")
        dates = QLabel(format_dates(playthrough))
        dates.setObjectName("cardDetails")
        hours = QLabel(f"{playthrough.hours_played:g} ore")
        hours.setObjectName("playthroughHours")

        text = QVBoxLayout()
        text.setSpacing(4)
        text.addWidget(title)
        text.addWidget(dates)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.addLayout(text, stretch=1)
        layout.addWidget(hours)


def create_section_title(text: str) -> QLabel:
    """Restituisce il titolo di una sezione della pagina."""
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def format_meta(catalog_game: CatalogGame) -> str:
    """Restituisce anno di uscita e generi, separati da un punto."""
    return " · ".join([format_release_year(catalog_game)] + catalog_game.genres)


def format_dates(playthrough: Playthrough) -> str:
    """Restituisce le date della partita in formato italiano, per esempio '10/06/2026 → 10/07/2026'."""
    if playthrough.start_date is None:
        return "date non indicate"
    text = f"dal {format_date(playthrough.start_date)}"
    if playthrough.completion_date is not None:
        text = f"{format_date(playthrough.start_date)} → {format_date(playthrough.completion_date)}"
    return text


def format_date(iso_date: str) -> str:
    """Trasforma una data ISO (2026-06-10) nel formato italiano (10/06/2026)."""
    year, month, day = iso_date.split("-")
    return f"{day}/{month}/{year}"
