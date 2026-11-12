"""Pagina Statistiche in stile "Wrapped": riquadri colorati, numeri enormi e la storia di come giochi."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.library import MAX_RATING
from core.repository import GameRepository
from core.wrapped import WrappedStats, activity_years, compute_wrapped
from ui.covers import CoverLabel
from ui.formatting import format_number

PAGE_MARGIN = 40
TWO_COLUMNS_WIDTH = 1000
TOP_COVER_SIZE = QSize(180, 240)
RANK_COVER_SIZE = QSize(42, 56)
PLATFORM_BARS = 4
BAR_STEPS = 1000
HOURS_PER_DAY = 24
FULL_WIDTH = 2


class Tile(QFrame):
    """Riquadro colorato della pagina; il colore ("tone") lo decide il QSS tramite una proprietà dinamica."""

    def __init__(self, tone: str) -> None:
        super().__init__()
        self.setObjectName("wrappedTile")
        self.setProperty("tone", tone)
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(28, 26, 28, 28)
        self.content.setSpacing(6)

    def add_text(self, text: str, style: str, wrap: bool = True) -> QLabel:
        """Aggiunge una riga di testo con uno degli stili della pagina (eyebrow, number, headline, body)."""
        label = QLabel(text)
        label.setObjectName(f"wrapped{style.capitalize()}")
        label.setWordWrap(wrap)
        self.content.addWidget(label)
        return label


class StatisticsPage(QWidget):
    """Racconta i numeri della libreria, per sempre oppure anno per anno."""

    def __init__(self, repository: GameRepository) -> None:
        super().__init__()
        self.repository = repository
        self.selected_year: int | None = None
        self.tiles: list[tuple[QWidget, int]] = []
        self.columns = 0

        heading = QLabel("Il tuo Questlog")
        heading.setObjectName("pageTitle")
        subtitle = QLabel("Come hai giocato, raccontato dai tuoi numeri.")
        subtitle.setObjectName("gameMeta")

        self.year_buttons = QButtonGroup(self)
        self.year_buttons.idClicked.connect(self.choose_year)
        self.year_row = QHBoxLayout()
        self.year_row.setSpacing(8)

        self.grid = QGridLayout()
        self.grid.setSpacing(20)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(PAGE_MARGIN, 28, PAGE_MARGIN, PAGE_MARGIN)
        content_layout.setSpacing(12)
        content_layout.addWidget(heading)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(8)
        content_layout.addLayout(self.year_row)
        content_layout.addSpacing(16)
        content_layout.addLayout(self.grid)
        content_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)

    def refresh(self) -> None:
        """Rilegge la libreria, ricrea i bottoni degli anni e i riquadri."""
        games = self.repository.load_games()
        years = activity_years(games)
        if self.selected_year not in years:
            self.selected_year = None
        self.create_year_buttons(years)
        self.show_stats(compute_wrapped(games, self.selected_year))

    def create_year_buttons(self, years: list[int]) -> None:
        """Crea le pillole "Di sempre" e una per ogni anno in cui hai giocato."""
        for old_button in self.year_buttons.buttons():
            self.year_buttons.removeButton(old_button)
            old_button.hide()
            old_button.deleteLater()
        while self.year_row.count():
            self.year_row.takeAt(0)
        for year in [0, *years]:
            button = QPushButton("Di sempre" if year == 0 else str(year))
            button.setObjectName("pillButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setChecked(year == (self.selected_year or 0))
            self.year_buttons.addButton(button, year)
            self.year_row.addWidget(button)
        self.year_row.addStretch()

    def choose_year(self, year: int) -> None:
        """Mostra le statistiche dell'anno cliccato (0 significa "di sempre")."""
        self.selected_year = year or None
        self.show_stats(compute_wrapped(self.repository.load_games(), self.selected_year))
        self.scroll_area.verticalScrollBar().setValue(0)

    def show_stats(self, stats: WrappedStats) -> None:
        """Ricrea tutti i riquadri; quelli senza dati da raccontare non compaiono."""
        for tile, _ in self.tiles:
            self.grid.removeWidget(tile)
            tile.hide()
            tile.deleteLater()

        if stats.games_played == 0:
            self.tiles = [(create_empty_tile(), FULL_WIDTH)]
        else:
            self.tiles = [(create_hero_tile(stats, self.selected_year), FULL_WIDTH)]
            self.tiles.append((create_top_game_tile(stats), 1))
            self.tiles.append((create_ranking_tile(stats), 1))
            self.tiles.append((create_platform_tile(stats), 1))
            self.tiles.append((create_completions_tile(stats), 1))
            if stats.average_rating is not None:
                self.tiles.append((create_rating_tile(stats), 1))
            if stats.median_days is not None:
                self.tiles.append((create_speed_tile(stats), 1))
            if stats.profile is not None:
                self.tiles.append((create_profile_tile(stats), FULL_WIDTH))
        self.columns = 0
        self.arrange_tiles()

    def arrange_tiles(self) -> None:
        """Dispone i riquadri su due colonne se c'è spazio; quelli FULL_WIDTH occupano tutta la riga."""
        columns = 2 if self.width() >= TWO_COLUMNS_WIDTH else 1
        if columns == self.columns:
            return
        self.columns = columns
        for tile, _ in self.tiles:
            self.grid.removeWidget(tile)
        row = column = 0
        for tile, span in self.tiles:
            span = min(span, columns)
            if column + span > columns:
                row, column = row + 1, 0
            self.grid.addWidget(tile, row, column, 1, span)
            column += span
            if column >= columns:
                row, column = row + 1, 0
        for index in range(2):
            self.grid.setColumnStretch(index, 1 if index < columns else 0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Quando la finestra cambia larghezza, decide di nuovo quante colonne usare."""
        super().resizeEvent(event)
        self.arrange_tiles()


def create_hero_tile(stats: WrappedStats, year: int | None) -> Tile:
    """Il riquadro d'apertura: le ore totali, raccontate in giorni."""
    tile = Tile("mint")
    tile.add_text(f"NEL {year} HAI GIOCATO" if year else "IN TUTTO HAI GIOCATO", "eyebrow")
    tile.add_text(f"{format_number(stats.total_hours)} ore", "number")
    days = round(stats.total_hours / HOURS_PER_DAY)
    games_text = "un gioco" if stats.games_played == 1 else f"{stats.games_played} giochi"
    if days >= 1:
        story = f"Sono {format_number(days)} giorni interi senza mai posare il controller, su {games_text}."
    else:
        story = f"Un inizio tranquillo: {games_text} e tante ore ancora da giocare."
    tile.add_text(story, "body")
    return tile


def create_top_game_tile(stats: WrappedStats) -> Tile:
    """Il gioco a cui hai dedicato più ore, con copertina e quota del tuo tempo."""
    top = stats.top_games[0]
    tile = Tile("coral")
    row = QHBoxLayout()
    row.setSpacing(24)
    row.addWidget(CoverLabel(top.game.cover_url, TOP_COVER_SIZE), alignment=Qt.AlignmentFlag.AlignTop)
    text = QVBoxLayout()
    text.setSpacing(6)
    for content, style in [
        ("IL GIOCO CHE TI HA PRESO DI PIÙ", "eyebrow"),
        (top.game.title, "headline"),
        (f"{format_number(top.hours)} ore", "number"),
        (f"{with_article(share(top.hours, stats.total_hours))} del tuo tempo", "body"),
    ]:
        label = QLabel(content)
        label.setObjectName(f"wrapped{style.capitalize()}")
        label.setWordWrap(True)
        text.addWidget(label)
    text.addStretch()
    row.addLayout(text, stretch=1)
    tile.content.addLayout(row)
    return tile


def create_ranking_tile(stats: WrappedStats) -> Tile:
    """La classifica dei giochi più giocati, con numero di posizione, copertina e ore."""
    tile = Tile("navy")
    tile.add_text("I TUOI TOP 5", "eyebrow")
    tile.content.addSpacing(8)
    for position, item in enumerate(stats.top_games, start=1):
        rank = QLabel(str(position))
        rank.setObjectName("wrappedRank")
        rank.setFixedWidth(34)
        title = QLabel(item.game.title)
        title.setObjectName("wrappedRankTitle")
        title.setWordWrap(True)
        hours = QLabel(f"{format_number(item.hours)} ore")
        hours.setObjectName("wrappedBody")
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(rank)
        row.addWidget(CoverLabel(item.game.cover_url, RANK_COVER_SIZE))
        row.addWidget(title, stretch=1)
        row.addWidget(hours)
        tile.content.addLayout(row)
    tile.content.addStretch()
    return tile


def create_platform_tile(stats: WrappedStats) -> Tile:
    """La piattaforma preferita in grande e, sotto, le barre delle altre."""
    favorite, favorite_hours = stats.platform_hours[0]
    tile = Tile("sky")
    tile.add_text("LA TUA CONSOLE", "eyebrow")
    tile.add_text(favorite, "headline")
    tile.add_text(f"{with_article(share(favorite_hours, stats.total_hours))} delle tue ore", "body")
    tile.content.addSpacing(10)
    for platform, hours in stats.platform_hours[:PLATFORM_BARS]:
        name = QLabel(platform)
        name.setObjectName("wrappedSmall")
        value = QLabel(f"{format_number(hours)} ore")
        value.setObjectName("wrappedSmall")
        labels = QHBoxLayout()
        labels.addWidget(name)
        labels.addStretch()
        labels.addWidget(value)
        bar = QProgressBar()
        bar.setObjectName("platformBar")
        bar.setTextVisible(False)
        bar.setRange(0, BAR_STEPS)
        bar.setValue(round(hours / favorite_hours * BAR_STEPS) if favorite_hours else 0)
        tile.content.addLayout(labels)
        tile.content.addWidget(bar)
    tile.content.addStretch()
    return tile


def create_completions_tile(stats: WrappedStats) -> Tile:
    """Le partite completate e quanto porti a termine di quello che inizi."""
    tile = Tile("gold")
    tile.add_text("TITOLI DI CODA", "eyebrow")
    tile.add_text(str(stats.completed), "number")
    tile.add_text("partite completate" if stats.completed != 1 else "partita completata", "headline")
    tile.add_text(f"{stats.playing} in corso · {stats.dropped} abbandonate", "body")
    if stats.completion_rate is not None:
        tile.add_text(
            f"Hai portato a termine {with_article(f'{stats.completion_rate:.0%}')} di quello che hai concluso.",
            "body",
        )
    tile.content.addStretch()
    return tile


def create_rating_tile(stats: WrappedStats) -> Tile:
    """Il voto medio e il gioco preferito."""
    tile = Tile("violet")
    tile.add_text("IL TUO VOTO MEDIO", "eyebrow")
    tile.add_text(f"{format_number(stats.average_rating or 0, decimals=1)} ★", "number")
    if stats.favorite_game is not None and stats.favorite_game.rating is not None:
        stars = int(stats.favorite_game.rating)
        tile.add_text("IL TUO PREFERITO", "eyebrow")
        tile.add_text(stats.favorite_game.title, "headline")
        tile.add_text("★" * stars + "☆" * (MAX_RATING - stars), "stars")
    tile.content.addStretch()
    return tile


def create_speed_tile(stats: WrappedStats) -> Tile:
    """Quanto ti dura un gioco e il record di velocità."""
    tile = Tile("ink")
    tile.add_text("UN GIOCO TI DURA", "eyebrow")
    tile.add_text(f"{format_number(stats.median_days or 0)} giorni", "number")
    tile.add_text("dalla prima partita ai titoli di coda, in media", "body")
    if stats.fastest is not None:
        game, days = stats.fastest
        day_text = "un giorno" if days == 1 else f"{days} giorni"
        tile.content.addSpacing(10)
        tile.add_text("IL TUO RECORD", "eyebrow")
        tile.add_text(f"{game.title} in {day_text}", "headline")
    tile.content.addStretch()
    return tile


def create_profile_tile(stats: WrappedStats) -> Tile:
    """Il profilo da giocatore, a chiusura della pagina."""
    tile = Tile("magenta")
    if stats.profile is not None:
        tile.add_text("IL TUO PROFILO DA GIOCATORE", "eyebrow")
        tile.add_text(stats.profile.title, "number")
        tile.add_text(stats.profile.description, "body")
    return tile


def create_empty_tile() -> Tile:
    """Riquadro mostrato quando non c'è ancora nessuna partita nel periodo scelto."""
    tile = Tile("navy")
    tile.add_text("ANCORA NIENTE DA RACCONTARE", "eyebrow")
    tile.add_text("Registra le tue partite", "headline")
    tile.add_text("Qui troverai le ore giocate, i tuoi giochi preferiti e che tipo di giocatore sei.", "body")
    return tile


def share(part: float, total: float) -> str:
    """Restituisce la percentuale di part su total, per esempio '80%'."""
    return f"{part / total:.0%}" if total else "0%"


def with_article(percentage: str) -> str:
    """Aggiunge l'articolo giusto davanti a una percentuale: "l'80%", "l'11%", ma "il 45%".

    In italiano si usa "l'" davanti ai numeri che si leggono con una vocale: uno, otto, undici.
    """
    number = percentage.rstrip("%")
    starts_with_vowel = number.startswith("8") or number in ("1", "11") or number.startswith("11")
    return f"l'{percentage}" if starts_with_vowel else f"il {percentage}"
