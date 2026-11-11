"""Form, dentro la pagina del gioco, per registrare una nuova partita."""

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.library import validate_new_playthrough
from core.models import Playthrough
from ui.widgets import HoursSpinBox

STATUS_CHOICES = [
    ("playing", "In corso"),
    ("completed", "Completata"),
    ("dropped", "Abbandonata"),
]
DATE_FORMAT = "dd/MM/yyyy"
ISO_FORMAT = "yyyy-MM-dd"
MAX_HOURS = 99999


class PlaythroughForm(QFrame):
    """Chiede piattaforma, stato, ore e date di una partita e la consegna con submitted se è valida."""

    submitted = Signal(Playthrough)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("formPanel")

        self.platform_input = QComboBox()
        self.platform_input.setEditable(True)
        platform_line = self.platform_input.lineEdit()
        if platform_line is not None:
            platform_line.setPlaceholderText("Scegli o scrivi una piattaforma")

        self.status_input = QComboBox()
        for status, label in STATUS_CHOICES:
            self.status_input.addItem(label, status)
        self.status_input.currentIndexChanged.connect(self.update_visible_fields)

        self.hours_input = HoursSpinBox()
        self.hours_input.setRange(0, MAX_HOURS)
        self.hours_input.setDecimals(1)
        self.hours_input.setSingleStep(0.5)
        self.hours_input.setSuffix(" ore")

        self.start_date_input = create_date_input()
        self.completion_date_input = create_date_input()
        self.start_date_input.dateChanged.connect(self.completion_date_input.setMinimumDate)

        self.form = QFormLayout()
        self.form.setHorizontalSpacing(20)
        self.form.setVerticalSpacing(14)
        self.form.addRow(create_form_label("Piattaforma"), self.platform_input)
        self.form.addRow(create_form_label("Stato"), self.status_input)
        self.form.addRow(create_form_label("Ore giocate"), self.hours_input)
        self.form.addRow(create_form_label("Iniziata il"), self.start_date_input)
        self.form.addRow(create_form_label("Completata il"), self.completion_date_input)

        self.error_label = QLabel()
        self.error_label.setObjectName("formError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.cancelled.emit)
        save_button = QPushButton("Salva partita")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.submit)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(cancel_button)
        actions.addWidget(save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addLayout(self.form)
        layout.addWidget(self.error_label)
        layout.addLayout(actions)

    def start(self, platform_suggestions: list[str]) -> None:
        """Svuota il form e propone le piattaforme indicate."""
        self.platform_input.clear()
        self.platform_input.addItems(platform_suggestions)
        self.platform_input.setCurrentText("")
        self.status_input.setCurrentIndex(0)
        self.hours_input.setValue(0)
        today = QDate.currentDate()
        for date_input in (self.start_date_input, self.completion_date_input):
            date_input.setMaximumDate(today)
            date_input.setDate(today)
        self.error_label.hide()
        self.update_visible_fields()
        self.platform_input.setFocus()

    def update_visible_fields(self) -> None:
        """Mostra la data di completamento solo per una partita completata."""
        self.form.setRowVisible(self.completion_date_input, self.selected_status() == "completed")

    def selected_status(self) -> str:
        """Restituisce lo stato scelto, come valore interno ("playing", "completed"...)."""
        return str(self.status_input.currentData())

    def submit(self) -> None:
        """Consegna la partita se i dati sono validi, altrimenti mostra il primo errore."""
        platform = self.platform_input.currentText().strip()
        error = "Indica la piattaforma su cui giochi." if platform == "" else None
        start_date = self.start_date_input.date().toString(ISO_FORMAT)
        completion_date = None
        if self.selected_status() == "completed":
            completion_date = self.completion_date_input.date().toString(ISO_FORMAT)
        if error is None:
            error = validate_new_playthrough(
                self.selected_status(), self.hours_input.value(), start_date, completion_date
            )
        if error is not None:
            self.error_label.setText(error)
            self.error_label.show()
            return
        self.submitted.emit(
            Playthrough(platform, self.selected_status(), self.hours_input.value(), start_date, completion_date)
        )


def create_form_label(text: str) -> QLabel:
    """Restituisce l'etichetta di un campo, alta quanto il campo e centrata in verticale."""
    label = QLabel(text)
    label.setObjectName("formLabel")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return label


def create_date_input() -> QDateEdit:
    """Restituisce un campo data con calendario e formato italiano."""
    date_input = QDateEdit()
    date_input.setCalendarPopup(True)
    date_input.setDisplayFormat(DATE_FORMAT)
    return date_input
