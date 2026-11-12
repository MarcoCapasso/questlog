"""Pagina di un gioco: dati dal catalogo IGDB, aggiunta alla libreria, voto e partite."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.catalog import CatalogGame, GameCatalog, find_library_game, game_from_catalog, link_to_catalog
from core.library import (
    calculate_total_hours,
    find_game_index_by_title,
    find_platform_spelling,
    is_backlog,
    known_platforms,
    remove_playthrough,
    replace_playthrough,
)
from core.models import Game, Playthrough
from core.repository import GameRepository
from core.translation import Translator, translate_summary
from ui.backdrop import BackdropWidget
from ui.carousel import ImageCarousel
from ui.covers import CoverLabel
from ui.game_card import PLAYTHROUGH_STATUS_LABELS, format_release_year
from ui.playthrough_form import PlaythroughForm
from ui.tasks import run_in_background
from ui.theme import ICONS_DIR
from ui.widgets import RatingInput

PAGE_MARGIN = 40
COVER_SIZE = QSize(210, 280)
SUMMARY_WIDTH = 680
NORMAL_PAGE = 0
CONFIRM_PAGE = 1
NOT_LINKED_HINT = "Cercalo in Aggiungi gioco per collegarlo a IGDB e vedere copertina e descrizione."


class GamePage(QWidget):
    """Mostra un gioco del catalogo o della libreria; se è in libreria permette di votarlo e registrare partite."""

    back_requested = Signal()
    library_changed = Signal()

    def __init__(self, repository: GameRepository, catalog: GameCatalog, translator: Translator) -> None:
        super().__init__()
        self.repository = repository
        self.catalog = catalog
        self.translator = translator
        self.details_loaded = False
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
        self.carousel = ImageCarousel(SUMMARY_WIDTH)
        self.screenshots_section = QWidget()
        screenshots_layout = QVBoxLayout(self.screenshots_section)
        screenshots_layout.setContentsMargins(0, 0, 0, 0)
        screenshots_layout.setSpacing(14)
        screenshots_layout.addWidget(create_section_title("Screenshot"))
        screenshots_layout.addWidget(self.carousel)
        self.screenshots_section.hide()

        self.add_button = QPushButton("Aggiungi alla libreria")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_to_library)
        self.in_library_chip = QLabel("Nella tua libreria")
        self.in_library_chip.setObjectName("libraryChip")
        self.rating_input = RatingInput()
        self.rating_input.rating_changed.connect(self.change_rating)
        actions = QHBoxLayout()
        actions.setSpacing(12)
        actions.addWidget(self.add_button)
        actions.addWidget(self.in_library_chip)
        actions.addStretch()
        actions.addWidget(self.rating_input)

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

        self.total_hours_label = QLabel()
        self.total_hours_label.setObjectName("gameMeta")

        self.new_playthrough_button = QPushButton("Nuova partita")
        self.new_playthrough_button.clicked.connect(lambda: self.open_playthrough_form(None))
        playthroughs_heading = QHBoxLayout()
        playthroughs_heading.addWidget(create_section_title("Partite"))
        playthroughs_heading.addStretch()
        playthroughs_heading.addWidget(self.new_playthrough_button)

        self.playthrough_list = QVBoxLayout()
        self.playthrough_list.setSpacing(10)
        self.playthrough_rows: list[PlaythroughRow] = []
        self.editing_index: int | None = None

        self.library_section = QWidget()
        self.library_section.setMaximumWidth(SUMMARY_WIDTH)
        library_layout = QVBoxLayout(self.library_section)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(14)
        library_layout.addLayout(playthroughs_heading)
        library_layout.addWidget(self.total_hours_label)
        library_layout.addLayout(self.playthrough_list)

        self.playthrough_form = PlaythroughForm()
        self.playthrough_form.setParent(self.library_section)
        self.playthrough_form.hide()
        self.playthrough_form.submitted.connect(self.save_playthrough)
        self.playthrough_form.cancelled.connect(self.close_playthrough_form)

        self.backdrop = BackdropWidget()
        content_layout = QVBoxLayout(self.backdrop)
        content_layout.setContentsMargins(PAGE_MARGIN, 20, PAGE_MARGIN, PAGE_MARGIN)
        content_layout.setSpacing(28)
        content_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        content_layout.addLayout(hero)
        content_layout.addWidget(self.summary_label)
        content_layout.addWidget(self.library_section)
        content_layout.addWidget(self.screenshots_section)
        content_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.backdrop)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)

    def show_catalog_game(self, catalog_game: CatalogGame) -> None:
        """Mostra un gioco scelto nel catalogo; se era già in libreria con lo stesso titolo, lo collega a IGDB."""
        self.games = self.repository.load_games()
        self.catalog_game = catalog_game
        self.game = find_library_game(self.games, catalog_game)
        if self.game is not None and self.game.igdb_id is None:
            link_to_catalog(self.game, catalog_game)
            self.save()
        self.start_view()
        self.load_details(catalog_game.igdb_id)

    def show_library_game(self, game: Game) -> None:
        """Mostra un gioco della libreria e, se è collegato a IGDB, ne scarica la descrizione."""
        self.games = self.repository.load_games()
        index = find_game_index_by_title(self.games, game.title)
        self.game = self.games[index] if index is not None else game
        self.catalog_game = None
        self.start_view()
        if self.game.igdb_id is not None:
            self.load_details(self.game.igdb_id)

    def start_view(self) -> None:
        """Riparte dall'alto della pagina, senza sfondo e immagini finché non arrivano i dettagli."""
        self.details_loaded = False
        self.close_playthrough_form()
        self.backdrop.set_url(None)
        self.carousel.set_images([])
        self.screenshots_section.hide()
        self.scroll_area.verticalScrollBar().setValue(0)
        self.update_view()

    def load_details(self, igdb_id: int) -> None:
        """Scarica in background i dettagli da IGDB (immagini e descrizione) e traduce la descrizione."""
        catalog = self.catalog
        translator = self.translator

        def fetch_details() -> CatalogGame | None:
            details = catalog.details(igdb_id)
            if details is not None:
                translate_summary(details, translator)
            return details

        run_in_background(fetch_details, self.on_details_loaded, self.ignore_error)

    def on_details_loaded(self, details: CatalogGame | None) -> None:
        """Completa la pagina con sfondo, immagini e descrizione, se riguardano ancora il gioco mostrato."""
        shown_id = self.catalog_game.igdb_id if self.catalog_game is not None else None
        if self.game is not None and self.game.igdb_id is not None:
            shown_id = self.game.igdb_id
        if details is None or details.igdb_id != shown_id:
            return
        self.catalog_game = details
        self.details_loaded = True
        self.backdrop.set_url(details.backdrop_url)
        self.carousel.set_images(details.screenshot_urls)
        self.screenshots_section.setVisible(bool(details.screenshot_urls))
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
        summary = catalog_game.summary if catalog_game is not None and self.details_loaded else ""
        self.summary_label.setText(summary)
        self.summary_label.setVisible(summary != "")

        in_library = self.game is not None
        self.add_button.setVisible(not in_library)
        self.in_library_chip.setVisible(in_library)
        self.rating_input.setVisible(self.game is not None and not is_backlog(self.game))
        self.library_section.setVisible(in_library)
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
        """Ricrea l'elenco delle partite, dalla più recente, con il totale delle ore.

        Il pannello del form non viene distrutto: viene chiuso, esce dall'elenco e ci rientra quando serve.
        """
        self.close_playthrough_form()
        while self.playthrough_list.count():
            item = self.playthrough_list.takeAt(0)
            old_widget = item.widget() if item is not None else None
            if old_widget is not None and old_widget is not self.playthrough_form:
                old_widget.hide()
                old_widget.deleteLater()
        self.playthrough_rows = []
        if not game.playthroughs:
            self.total_hours_label.setText("Non l'hai ancora iniziato.")
            return
        self.total_hours_label.setText(f"{calculate_total_hours(game):g} ore in totale")
        for index in reversed(range(len(game.playthroughs))):
            row = PlaythroughRow(game.playthroughs[index])
            row.edit_requested.connect(lambda chosen=index: self.open_playthrough_form(chosen))
            row.delete_confirmed.connect(lambda chosen=index: self.delete_playthrough(chosen))
            self.playthrough_list.addWidget(row)
            self.playthrough_rows.append(row)

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

    def open_playthrough_form(self, playthrough_index: int | None) -> None:
        """Apre il pannello: in cima all'elenco per una nuova partita, al posto della riga per modificarne una."""
        if self.game is None:
            return
        self.close_playthrough_form()
        self.editing_index = playthrough_index
        game_platforms = list(self.catalog_game.platforms) if self.catalog_game is not None else []
        self.platform_suggestions = game_platforms
        playthrough = None if playthrough_index is None else self.game.playthroughs[playthrough_index]
        self.playthrough_form.start(game_platforms, known_platforms(self.games), playthrough)

        position = 0
        if playthrough_index is not None:
            position = len(self.game.playthroughs) - 1 - playthrough_index
            self.playthrough_rows[position].hide()
        self.playthrough_list.insertWidget(position, self.playthrough_form)
        self.playthrough_form.show()

    def close_playthrough_form(self) -> None:
        """Chiude il pannello e rimette al suo posto la riga che si stava modificando."""
        self.playthrough_form.hide()
        self.playthrough_list.removeWidget(self.playthrough_form)
        self.editing_index = None
        for row in self.playthrough_rows:
            row.show()

    def save_playthrough(self, playthrough: Playthrough) -> None:
        """Aggiunge la nuova partita o sostituisce quella modificata, con la grafia già nota della piattaforma."""
        if self.game is None:
            return
        playthrough.platform = find_platform_spelling(self.games, playthrough.platform)
        for suggestion in self.platform_suggestions:
            if suggestion.lower() == playthrough.platform.lower():
                playthrough.platform = suggestion
        if self.editing_index is None:
            self.game.playthroughs.append(playthrough)
        else:
            replace_playthrough(self.game, self.editing_index, playthrough)
        self.close_playthrough_form()
        self.save()
        self.update_view()

    def delete_playthrough(self, playthrough_index: int) -> None:
        """Elimina la partita; se era l'ultima il gioco torna da giocare e perde il voto."""
        if self.game is None:
            return
        remove_playthrough(self.game, playthrough_index)
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
                self.close_playthrough_form()
            else:
                self.back_requested.emit()
            return
        super().keyPressEvent(event)


class PlaythroughRow(QFrame):
    """Una riga dell'elenco partite: piattaforma, stato, date, note, ore e i bottoni per modificarla o eliminarla.

    L'eliminazione chiede conferma nella riga stessa: ore e bottoni lasciano il posto a "Eliminare? Annulla / Elimina".
    """

    edit_requested = Signal()
    delete_confirmed = Signal()

    def __init__(self, playthrough: Playthrough) -> None:
        super().__init__()
        self.setObjectName("playthroughRow")
        self.setMaximumWidth(SUMMARY_WIDTH)

        title = QLabel(f"{playthrough.platform} · {PLAYTHROUGH_STATUS_LABELS[playthrough.status]}")
        title.setObjectName("cardTitle")
        dates = QLabel(format_dates(playthrough))
        dates.setObjectName("cardDetails")
        text = QVBoxLayout()
        text.setSpacing(4)
        text.addWidget(title)
        text.addWidget(dates)
        if playthrough.notes:
            notes = QLabel(playthrough.notes)
            notes.setObjectName("playthroughNotes")
            notes.setWordWrap(True)
            text.addWidget(notes)

        hours = QLabel(f"{playthrough.hours_played:g} ore")
        hours.setObjectName("playthroughHours")
        edit_button = create_row_action("pencil.svg", "Modifica partita")
        edit_button.clicked.connect(self.edit_requested.emit)
        delete_button = create_row_action("trash.svg", "Elimina partita")
        delete_button.clicked.connect(self.ask_confirmation)
        normal_actions = QWidget()
        normal_layout = QHBoxLayout(normal_actions)
        normal_layout.setContentsMargins(0, 0, 0, 0)
        normal_layout.setSpacing(4)
        normal_layout.addWidget(hours)
        normal_layout.addSpacing(12)
        normal_layout.addWidget(edit_button)
        normal_layout.addWidget(delete_button)

        question = QLabel("Eliminare la partita?")
        question.setObjectName("confirmQuestion")
        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.cancel_confirmation)
        confirm_button = QPushButton("Elimina")
        confirm_button.setObjectName("dangerButton")
        confirm_button.clicked.connect(self.delete_confirmed.emit)
        confirm_actions = QWidget()
        confirm_layout = QHBoxLayout(confirm_actions)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(8)
        confirm_layout.addWidget(question)
        confirm_layout.addWidget(cancel_button)
        confirm_layout.addWidget(confirm_button)

        self.action_pages = QStackedWidget()
        self.action_pages.addWidget(normal_actions)
        self.action_pages.addWidget(confirm_actions)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 12, 16)
        layout.setSpacing(16)
        layout.addLayout(text, stretch=1)
        layout.addWidget(self.action_pages)
        self.show_action_page(NORMAL_PAGE)

    def ask_confirmation(self) -> None:
        """Al posto di ore e bottoni mostra la domanda di conferma."""
        self.show_action_page(CONFIRM_PAGE)

    def cancel_confirmation(self) -> None:
        """Torna a ore e bottoni, senza eliminare nulla."""
        self.show_action_page(NORMAL_PAGE)

    def show_action_page(self, page_index: int) -> None:
        """Mostra una delle due pagine di azioni e adatta la larghezza a quella visibile.

        Un QStackedWidget è largo quanto la sua pagina più grande: dando alle pagine nascoste
        la politica Ignored, conta solo quella visibile.
        """
        for index in range(self.action_pages.count()):
            policy = QSizePolicy.Policy.Preferred if index == page_index else QSizePolicy.Policy.Ignored
            page = self.action_pages.widget(index)
            if page is not None:
                page.setSizePolicy(policy, policy)
        self.action_pages.setCurrentIndex(page_index)
        self.action_pages.adjustSize()
        self.setProperty("confirming", page_index == CONFIRM_PAGE)
        self.style().unpolish(self)
        self.style().polish(self)


def create_row_action(icon_name: str, tooltip: str) -> QToolButton:
    """Restituisce un bottone rotondo con un'icona, per le azioni su una riga."""
    button = QToolButton()
    button.setObjectName("rowAction")
    button.setIcon(QIcon(str(ICONS_DIR / icon_name)))
    button.setIconSize(QSize(18, 18))
    button.setToolTip(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


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
