"""Card di un gioco nella griglia della libreria."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from core.library import calculate_total_hours, summary_status
from core.models import Game

STATUS_LABELS = {
    "playing": "In corso",
    "completed": "Completato",
    "dropped": "Abbandonato",
    "backlog": "Backlog",
}
CARD_WIDTH = 160


class GameCard(QFrame):
    """Copertina, stato, titolo e ore di un gioco."""

    def __init__(self, game: Game) -> None:
        super().__init__()
        self.setObjectName("gameCard")
        self.setFixedWidth(CARD_WIDTH)

        cover = QLabel()
        cover.setObjectName("cover")
        cover.setFixedSize(CARD_WIDTH, CARD_WIDTH * 4 // 3)

        status = summary_status(game)
        status_chip = QLabel(STATUS_LABELS[status])
        status_chip.setObjectName("statusChip")
        status_chip.setProperty("status", status)

        title = QLabel(game.title)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)

        details = QLabel(format_card_details(game))
        details.setObjectName("cardDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(cover)
        layout.addWidget(status_chip, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(details)
        layout.addStretch()


def format_card_details(game: Game) -> str:
    """Restituisce la riga sotto il titolo: ore giocate e voto, oppure 'mai iniziato'."""
    if summary_status(game) == "backlog":
        return "mai iniziato"
    details = f"{calculate_total_hours(game):g} ore"
    if game.rating is not None:
        details += f" · voto {game.rating:g}"
    return details