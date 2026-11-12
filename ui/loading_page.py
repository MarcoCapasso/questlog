"""Pagina d'attesa: mentre si controlla la sessione o si scarica la libreria, con "Riprova" se qualcosa va storto."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class LoadingPage(QWidget):
    """Un messaggio al centro e, solo dopo un errore, il bottone per riprovare."""

    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.message = QLabel()
        self.message.setObjectName("sectionMessage")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)
        self.retry_button = QPushButton("Riprova")
        self.retry_button.setObjectName("primaryButton")
        self.retry_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_button.clicked.connect(self.retry_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.addStretch()
        layout.addWidget(self.message)
        layout.addWidget(self.retry_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        self.show_message("Un attimo…")

    def show_message(self, text: str) -> None:
        """Mostra un messaggio d'attesa, senza bottone."""
        self.message.setText(text)
        self.retry_button.hide()

    def show_error(self, text: str) -> None:
        """Mostra cosa non è andato e il bottone "Riprova"."""
        self.message.setText(text)
        self.retry_button.show()
