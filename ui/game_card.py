"""Card di un gioco nella griglia della libreria."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from core.library import calculate_total_hours, playthrough_statuses, summary_status
from core.models import Game

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

        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.addWidget(status_chip)
        other_statuses_count = len(playthrough_statuses(game)) - 1
        if other_statuses_count > 0:
            extra_chip = QLabel(f"+{other_statuses_count}")
            extra_chip.setObjectName("extraChip")
            extra_chip.setToolTip(format_playthroughs_tooltip(game))
            chips.addWidget(extra_chip)
        chips.addStretch()

        title = QLabel(game.title)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)

        details = QLabel(format_card_details(game))
        details.setObjectName("cardDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(cover)
        layout.addLayout(chips)
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


def format_playthroughs_tooltip(game: Game) -> str:
    """Restituisce l'elenco delle partite, una per riga, con piattaforma e stato."""
    lines = []
    for playthrough in game.playthroughs:
        lines.append(f"{playthrough.platform} · {PLAYTHROUGH_STATUS_LABELS[playthrough.status]}")
    return "\n".join(lines)