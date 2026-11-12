"""Pagina che propone di caricare nell'account la libreria salvata su questo computer (una volta sola)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from core.cloud_repository import SupabaseGameRepository, split_valid_games
from core.models import Game
from core.storage import mark_library_uploaded
from ui.tasks import run_in_background

PANEL_WIDTH = 520
PREVIEW_TITLES = 5


class UploadPage(QWidget):
    """Mostra i giochi trovati sul PC e li carica nell'account; emette done con la libreria da usare."""

    done = Signal(object)

    def __init__(self, remote: SupabaseGameRepository) -> None:
        super().__init__()
        self.remote = remote
        self.valid_games: list[Game] = []

        self.title = QLabel()
        self.title.setObjectName("authTitle")
        self.title.setWordWrap(True)
        explanation = QLabel(
            "Vuoi caricarli nel tuo account? Li ritroverai su ogni computer. "
            "Il file su questo PC non viene cancellato: resta come copia."
        )
        explanation.setObjectName("gameMeta")
        explanation.setWordWrap(True)
        self.preview = QLabel()
        self.preview.setObjectName("fieldCaption")
        self.preview.setWordWrap(True)
        self.problems = QLabel()
        self.problems.setObjectName("authMessage")
        self.problems.setProperty("error", True)
        self.problems.setWordWrap(True)
        self.message = QLabel()
        self.message.setObjectName("authMessage")
        self.message.setWordWrap(True)

        self.upload_button = QPushButton()
        self.upload_button.setObjectName("primaryButton")
        self.upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_button.clicked.connect(self.start_upload)
        self.skip_button = QPushButton("Non adesso, parto da zero")
        self.skip_button.setObjectName("textButton")
        self.skip_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_button.clicked.connect(lambda: self.done.emit([]))

        panel = QFrame()
        panel.setObjectName("formPanel")
        panel.setFixedWidth(PANEL_WIDTH)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(32, 30, 32, 26)
        panel_layout.setSpacing(14)
        for widget in (self.title, explanation, self.preview, self.problems, self.message, self.upload_button):
            panel_layout.addWidget(widget)
        panel_layout.addWidget(self.skip_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(panel)
        row.addStretch()
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 28, 40, 40)
        content_layout.addStretch(1)
        content_layout.addLayout(row)
        content_layout.addStretch(2)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)

    def start(self, local_games: list[Game]) -> None:
        """Prepara la proposta: quanti giochi, quali, e quali il database rifiuterebbe."""
        self.valid_games, problems = split_valid_games(local_games)
        count = len(local_games)
        self.title.setText(f"Hai {count} {'gioco' if count == 1 else 'giochi'} su questo computer")
        titles = [game.title for game in self.valid_games[:PREVIEW_TITLES]]
        others = len(self.valid_games) - len(titles)
        self.preview.setText(", ".join(titles) + (f" e altri {others}" if others > 0 else ""))
        self.problems.setText(
            "Questi non si possono caricare e restano solo nella copia sul PC:\n• " + "\n• ".join(problems)
        )
        self.problems.setVisible(bool(problems))
        valid_count = len(self.valid_games)
        self.upload_button.setText(f"Carica {valid_count} {'gioco' if valid_count == 1 else 'giochi'}")
        self.upload_button.setVisible(valid_count > 0)
        self.set_busy(False)
        self.show_message("")

    def show_message(self, text: str, error: bool = False) -> None:
        """Mostra un messaggio sopra il bottone (rosso se è un errore); con il testo vuoto lo nasconde."""
        self.message.setText(text)
        self.message.setProperty("error", error)
        self.message.style().unpolish(self.message)
        self.message.style().polish(self.message)
        self.message.setVisible(text != "")

    def set_busy(self, busy: bool) -> None:
        """Durante il caricamento i bottoni si disattivano."""
        self.upload_button.setEnabled(not busy)
        self.skip_button.setEnabled(not busy)

    def start_upload(self) -> None:
        """Manda i giochi validi nell'account, in background."""
        self.set_busy(True)
        self.show_message("Carico la libreria…")
        games = self.valid_games
        run_in_background(lambda: self.remote.upload_games(games), self.on_uploaded, self.on_upload_failed)

    def on_uploaded(self, _result: object) -> None:
        """Caricamento riuscito: il file locale diventa una copia e si entra con la libreria caricata."""
        mark_library_uploaded()
        self.done.emit(self.valid_games)

    def on_upload_failed(self, message: str) -> None:
        """Caricamento non riuscito: niente è cambiato, si può riprovare."""
        self.set_busy(False)
        self.show_message(message, error=True)
