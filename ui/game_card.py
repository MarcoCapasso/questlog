"""Card cliccabili dei giochi: quelle della libreria e quelle del catalogo IGDB."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.catalog import CatalogGame
from core.library import calculate_total_hours, playthrough_statuses, summary_status
from core.models import Game
from ui.covers import CoverLabel

STATUS_LABELS = {
    "playing": "In corso",
    "completed": "Completato",
    "dropped": "Abbandonato",
    "backlog": "Da giocare",
}
PLAYTHROUGH_STATUS_LABELS = {
    "playing": "in corso",
    "completed": "completata",
    "dropped": "abbandonata",
}
CARD_WIDTH = 160
COVER_SIZE = QSize(CARD_WIDTH, CARD_WIDTH * 4 // 3)


class ClickableCard(QFrame):
    """Base delle card: copertina in alto, contenuto sotto, e il segnale clicked quando la si clicca."""

    clicked = Signal()

    def __init__(self, cover_url: str | None) -> None:
        super().__init__()
        self.setObjectName("gameCard")
        self.setFixedWidth(CARD_WIDTH)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(8)
        self.content.addWidget(CoverLabel(cover_url, COVER_SIZE))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Un click sinistro rilasciato sopra la card emette clicked."""
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class GameCard(ClickableCard):
    """Card di un gioco della libreria: copertina, stato, titolo, ore e voto."""

    def __init__(self, game: Game) -> None:
        super().__init__(game.cover_url)
        status = summary_status(game)
        status_chip = create_chip(STATUS_LABELS[status], "statusChip")
        status_chip.setProperty("status", status)

        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.addWidget(status_chip)
        other_statuses_count = len(playthrough_statuses(game)) - 1
        if other_statuses_count > 0:
            extra_chip = create_chip(f"+{other_statuses_count}", "extraChip")
            extra_chip.setToolTip(format_playthroughs_tooltip(game))
            chips.addWidget(extra_chip)
        chips.addStretch()

        self.content.addLayout(chips)
        self.content.addWidget(create_card_title(game.title))
        self.content.addWidget(create_card_details(format_card_details(game)))
        self.content.addStretch()


class CatalogCard(ClickableCard):
    """Card di un gioco del catalogo: copertina, titolo, anno e, se c'è, il segno "In libreria"."""

    def __init__(self, catalog_game: CatalogGame, in_library: bool) -> None:
        super().__init__(catalog_game.cover_url)
        if in_library:
            chips = QHBoxLayout()
            chips.addWidget(create_chip("In libreria", "libraryChip"))
            chips.addStretch()
            self.content.addLayout(chips)
        self.content.addWidget(create_card_title(catalog_game.title))
        self.content.addWidget(create_card_details(format_release_year(catalog_game)))
        self.content.addStretch()


def create_chip(text: str, object_name: str) -> QLabel:
    """Restituisce un'etichetta a pillola con lo stile indicato dal nome."""
    chip = QLabel(text)
    chip.setObjectName(object_name)
    return chip


def create_card_title(text: str) -> QLabel:
    """Restituisce il titolo della card, che va a capo se è lungo."""
    title = QLabel(text)
    title.setObjectName("cardTitle")
    title.setWordWrap(True)
    return title


def create_card_details(text: str) -> QWidget:
    """Restituisce la riga grigia sotto il titolo."""
    details = QLabel(text)
    details.setObjectName("cardDetails")
    return details


def format_card_details(game: Game) -> str:
    """Restituisce la riga sotto il titolo: ore giocate e voto, oppure 'mai iniziato'."""
    if summary_status(game) == "backlog":
        return "mai iniziato"
    details = f"{calculate_total_hours(game):g} ore"
    if game.rating is not None:
        details += f" · voto {game.rating:g}"
    return details


def format_release_year(catalog_game: CatalogGame) -> str:
    """Restituisce l'anno di uscita, oppure 'data da annunciare'."""
    if catalog_game.release_year is None:
        return "data da annunciare"
    return str(catalog_game.release_year)


def format_playthroughs_tooltip(game: Game) -> str:
    """Restituisce l'elenco delle partite, una per riga, con piattaforma e stato."""
    lines = []
    for playthrough in game.playthroughs:
        lines.append(f"{playthrough.platform} · {PLAYTHROUGH_STATUS_LABELS[playthrough.status]}")
    return "\n".join(lines)
