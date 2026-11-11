"""Finestra di dialogo per aggiungere un gioco alla libreria."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from core.library import validate_new_title
from core.models import Game


class AddGameDialog(QDialog):
    """Chiede i dati di un nuovo gioco e li accetta solo se sono validi."""

    def __init__(self, games: list[Game], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.games = games
        self.setWindowTitle("Aggiungi gioco")
        self.setMinimumWidth(440)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Es. Hollow Knight")

        self.error_label = QLabel()
        self.error_label.setObjectName("formError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        form = QFormLayout()
        form.addRow("Titolo", self.title_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salva")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annulla")
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def validate_and_accept(self) -> None:
        """Chiude la finestra solo se i dati sono validi, altrimenti mostra l'errore."""
        error = validate_new_title(self.games, self.title_input.text())
        if error is not None:
            self.error_label.setText(error)
            self.error_label.show()
            self.title_input.setFocus()
            return
        self.accept()

    def created_game(self) -> Game:
        """Restituisce il gioco con i dati inseriti."""
        return Game(self.title_input.text().strip())
    