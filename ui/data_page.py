"""Pagina "I tuoi dati": esportare la libreria in CSV e ripristinarla da un file, tutto dentro la finestra.

L'unica finestra che si apre è quella di sistema di Windows per scegliere il file (QFileDialog).
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.csv_io import export_csv, import_csv
from core.library import today_iso
from core.models import Game
from core.repository import GameRepository

PAGE_MARGIN = 40
PANEL_WIDTH = 680
DEFAULT_FILE_NAME = "questlog.csv"
CSV_FILTER = "File CSV (*.csv)"


class DataPage(QWidget):
    """Esporta e importa la libreria; emette library_replaced dopo un import confermato."""

    library_replaced = Signal()

    def __init__(self, repository: GameRepository) -> None:
        super().__init__()
        self.repository = repository
        self.pending_games: list[Game] | None = None

        heading = QLabel("I tuoi dati")
        heading.setObjectName("pageTitle")
        subtitle = QLabel("Porta la tua libreria fuori da Questlog, oppure ripristinala da un backup.")
        subtitle.setObjectName("gameMeta")

        export_button = QPushButton("Esporta in CSV…")
        export_button.setObjectName("primaryButton")
        export_button.clicked.connect(self.choose_export_file)
        self.export_message = create_message()
        export_panel = Panel(
            "Esporta la libreria",
            "Salva tutti i giochi e le partite in un file CSV: puoi aprirlo con Excel o tenerlo come backup.",
        )
        export_panel.body.addWidget(export_button, alignment=Qt.AlignmentFlag.AlignLeft)
        export_panel.body.addWidget(self.export_message)

        choose_button = QPushButton("Scegli un file…")
        choose_button.clicked.connect(self.choose_import_file)
        self.import_message = create_message()
        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewText")
        self.preview_label.setWordWrap(True)
        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.cancel_import)
        confirm_button = QPushButton("Sostituisci la libreria")
        confirm_button.setObjectName("dangerButton")
        confirm_button.clicked.connect(self.confirm_import)
        preview_actions = QHBoxLayout()
        preview_actions.addStretch()
        preview_actions.addWidget(cancel_button)
        preview_actions.addWidget(confirm_button)
        self.preview = QFrame()
        self.preview.setObjectName("importPreview")
        preview_layout = QVBoxLayout(self.preview)
        preview_layout.setContentsMargins(18, 16, 18, 16)
        preview_layout.setSpacing(12)
        preview_layout.addWidget(self.preview_label)
        preview_layout.addLayout(preview_actions)
        self.preview.hide()
        import_panel = Panel(
            "Importa da CSV",
            "Ripristina la libreria da un file esportato da Questlog. Prima di cambiare qualcosa "
            "ti mostro cosa contiene il file e chiedo conferma.",
        )
        import_panel.body.addWidget(choose_button, alignment=Qt.AlignmentFlag.AlignLeft)
        import_panel.body.addWidget(self.preview)
        import_panel.body.addWidget(self.import_message)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(PAGE_MARGIN, 28, PAGE_MARGIN, PAGE_MARGIN)
        content_layout.setSpacing(12)
        content_layout.addWidget(heading)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(16)
        content_layout.addWidget(export_panel)
        content_layout.addSpacing(8)
        content_layout.addWidget(import_panel)
        content_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)

    def start(self) -> None:
        """Riparte da zero ogni volta che si apre la pagina: niente messaggi vecchi né anteprime in sospeso."""
        self.export_message.hide()
        self.import_message.hide()
        self.cancel_import()

    def choose_export_file(self) -> None:
        """Chiede dove salvare il file con la finestra di sistema, poi esporta."""
        default_path = Path.home() / "Documents" / DEFAULT_FILE_NAME
        file_name, _ = QFileDialog.getSaveFileName(self, "Esporta la libreria", str(default_path), CSV_FILTER)
        if file_name:
            self.export_to(Path(file_name))

    def export_to(self, path: Path) -> None:
        """Esporta la libreria nel file indicato e mostra com'è andata."""
        games = self.repository.load_games()
        try:
            export_csv(games, path)
        except OSError as error:
            show_message(self.export_message, f"Non sono riuscito a salvare il file: {error.strerror}.", error=True)
            return
        playthrough_count = sum(len(game.playthroughs) for game in games)
        show_message(
            self.export_message,
            f"Esportati {len(games)} giochi e {playthrough_count} partite in {path.name}.",
        )

    def choose_import_file(self) -> None:
        """Chiede quale file importare con la finestra di sistema, poi mostra l'anteprima."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Importa la libreria", str(Path.home()), CSV_FILTER)
        if file_name:
            self.preview_import(Path(file_name))

    def preview_import(self, path: Path) -> None:
        """Legge e controlla il file; se è valido mostra cosa contiene e chiede conferma, senza toccare la libreria."""
        self.cancel_import()
        self.import_message.hide()
        try:
            games = import_csv(today_iso(), path)
        except UnicodeDecodeError:
            show_message(self.import_message, "Il file non è in UTF-8: da Excel salvalo come \"CSV UTF-8\".", True)
            return
        except ValueError as error:
            show_message(self.import_message, f"File non importato, la libreria non è cambiata. {error}", True)
            return
        except OSError as error:
            show_message(self.import_message, f"Non sono riuscito ad aprire il file: {error.strerror}.", True)
            return

        self.pending_games = games
        current_count = len(self.repository.load_games())
        playthrough_count = sum(len(game.playthroughs) for game in games)
        self.preview_label.setText(
            f"«{path.name}» contiene {len(games)} giochi e {playthrough_count} partite.\n"
            f"La tua libreria attuale ({current_count} giochi) verrà sostituita."
        )
        self.preview.show()

    def confirm_import(self) -> None:
        """Sostituisce la libreria con i giochi del file e avvisa la finestra.

        Senza un'anteprima riuscita non fa nulla: una lista vuota cancellerebbe la libreria.
        """
        games = self.pending_games
        if games is None:
            return
        self.repository.save_games(games)
        self.cancel_import()
        show_message(self.import_message, f"Libreria importata: {len(games)} giochi.")
        self.library_replaced.emit()

    def cancel_import(self) -> None:
        """Chiude l'anteprima senza cambiare nulla."""
        self.pending_games = None
        self.preview.hide()


class Panel(QFrame):
    """Riquadro con titolo e spiegazione; body è il suo layout verticale, dove aggiungere il resto.

    Non si chiama "layout" perché QWidget ha già un metodo layout(): lo nasconderemmo.
    """

    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self.setObjectName("formPanel")
        self.setMaximumWidth(PANEL_WIDTH)
        title_label = QLabel(title)
        title_label.setObjectName("formTitle")
        description_label = QLabel(description)
        description_label.setObjectName("gameMeta")
        description_label.setWordWrap(True)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(24, 20, 24, 24)
        self.body.setSpacing(12)
        self.body.addWidget(title_label)
        self.body.addWidget(description_label)
        self.body.addSpacing(4)


def create_message() -> QLabel:
    """Restituisce l'etichetta, inizialmente nascosta, per l'esito di un'operazione."""
    label = QLabel()
    label.setWordWrap(True)
    label.hide()
    return label


def show_message(label: QLabel, text: str, error: bool = False) -> None:
    """Mostra un esito: verde se è andato tutto bene, rosso se c'è stato un errore."""
    label.setObjectName("formError" if error else "successMessage")
    label.style().unpolish(label)
    label.style().polish(label)
    label.setText(text)
    label.show()
