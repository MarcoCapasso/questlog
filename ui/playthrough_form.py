"""Pannello, dentro la pagina del gioco, per registrare una nuova partita."""

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCompleter,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.library import validate_new_playthrough
from core.models import Playthrough
from ui.flow_layout import FlowLayout
from ui.widgets import DateInput, HoursInput

STATUS_CHOICES = [
    ("playing", "In corso"),
    ("completed", "Completata"),
    ("dropped", "Abbandonata"),
]
ISO_FORMAT = "yyyy-MM-dd"
PLATFORM_INPUT_WIDTH = 300


class PlaythroughForm(QFrame):
    """Chiede piattaforma, stato, ore e date di una partita e la consegna con submitted se è valida."""

    submitted = Signal(Playthrough)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("formPanel")

        self.title_label = QLabel()
        self.title_label.setObjectName("formTitle")
        close_button = QToolButton()
        close_button.setObjectName("closeButton")
        close_button.setText("✕")
        close_button.setToolTip("Chiudi")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.cancelled.emit)
        title_row = QHBoxLayout()
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        title_row.addWidget(close_button)

        self.platform_buttons = QButtonGroup(self)
        platform_pills_container = QWidget()
        self.platform_pills = FlowLayout(platform_pills_container)
        self.platform_input = QLineEdit()
        self.platform_input.setObjectName("formInput")
        self.platform_input.setPlaceholderText("Es. PC, PS5, Nintendo Switch")
        self.platform_input.setFixedWidth(PLATFORM_INPUT_WIDTH)
        platform_layout = QVBoxLayout()
        platform_layout.setSpacing(8)
        platform_layout.addWidget(platform_pills_container)
        platform_layout.addWidget(self.platform_input)

        self.status_buttons = QButtonGroup(self)
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        for index, (status, label) in enumerate(STATUS_CHOICES):
            button = create_pill(label)
            button.setProperty("status", status)
            self.status_buttons.addButton(button, index)
            status_row.addWidget(button)
        status_row.addStretch()
        self.status_buttons.idClicked.connect(self.update_visible_fields)

        self.hours_input = HoursInput()
        self.start_date_input = DateInput()
        self.completion_date_input = DateInput()
        self.start_date_input.dateChanged.connect(self.completion_date_input.setMinimumDate)
        self.completion_caption = create_caption("Completata il")

        numbers = QGridLayout()
        numbers.setHorizontalSpacing(16)
        numbers.setVerticalSpacing(8)
        numbers.addWidget(create_caption("Ore giocate"), 0, 0)
        numbers.addWidget(create_caption("Iniziata il"), 0, 1)
        numbers.addWidget(self.completion_caption, 0, 2)
        numbers.addWidget(self.hours_input, 1, 0)
        numbers.addWidget(self.start_date_input, 1, 1)
        numbers.addWidget(self.completion_date_input, 1, 2)
        for column in range(3):
            numbers.setColumnStretch(column, 1)

        self.error_label = QLabel()
        self.error_label.setObjectName("formError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.cancelled.emit)
        self.save_button = QPushButton()
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.submit)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(cancel_button)
        actions.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(10)
        layout.addLayout(title_row)
        layout.addSpacing(6)
        layout.addWidget(create_caption("Piattaforma"))
        layout.addLayout(platform_layout)
        layout.addSpacing(10)
        layout.addWidget(create_caption("Stato"))
        layout.addLayout(status_row)
        layout.addSpacing(10)
        layout.addLayout(numbers)
        layout.addWidget(self.error_label)
        layout.addSpacing(6)
        layout.addLayout(actions)

    def start(
        self,
        game_platforms: list[str],
        known_platforms: list[str],
        playthrough: Playthrough | None = None,
    ) -> None:
        """Prepara il pannello: vuoto per una nuova partita, già compilato se riceve la partita da modificare.

        Se IGDB indica le piattaforme del gioco, si sceglie solo tra quelle (già selezionata se è una sola).
        Altrimenti si scrive la piattaforma, con i suggerimenti presi da quelle già usate in libreria.
        """
        editing = playthrough is not None
        self.title_label.setText("Modifica partita" if editing else "Nuova partita")
        self.save_button.setText("Salva modifiche" if editing else "Salva partita")

        self.create_platform_buttons(game_platforms)
        if len(game_platforms) == 1:
            self.platform_buttons.buttons()[0].setChecked(True)
        self.platform_input.clear()
        self.platform_input.setVisible(not game_platforms)
        completer = QCompleter(known_platforms, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.platform_input.setCompleter(completer)

        self.status_buttons.button(0).setChecked(True)
        self.hours_input.set_value(0)
        today = QDate.currentDate()
        for date_input in (self.start_date_input, self.completion_date_input):
            date_input.setMaximumDate(today)
            date_input.setDate(today)
        self.error_label.hide()
        if playthrough is not None:
            self.fill(playthrough)
        self.update_visible_fields()

    def fill(self, playthrough: Playthrough) -> None:
        """Riempie i campi con i dati della partita da modificare."""
        self.select_platform(playthrough.platform)
        statuses = [status for status, _ in STATUS_CHOICES]
        self.status_buttons.button(statuses.index(playthrough.status)).setChecked(True)
        self.hours_input.set_value(playthrough.hours_played)
        if playthrough.start_date is not None:
            self.start_date_input.setDate(QDate.fromString(playthrough.start_date, ISO_FORMAT))
        if playthrough.completion_date is not None:
            self.completion_date_input.setDate(QDate.fromString(playthrough.completion_date, ISO_FORMAT))

    def select_platform(self, platform: str) -> None:
        """Seleziona la pillola con quel nome; se non c'è (per esempio "PS4" scritto a mano), la mette nel campo."""
        for button in self.platform_buttons.buttons():
            if button.text().lower() == platform.lower():
                button.setChecked(True)
                return
        self.platform_buttons.setExclusive(False)
        for button in self.platform_buttons.buttons():
            button.setChecked(False)
        self.platform_buttons.setExclusive(True)
        self.platform_input.setText(platform)
        self.platform_input.show()

    def create_platform_buttons(self, platforms: list[str]) -> None:
        """Sostituisce le pillole delle piattaforme con quelle indicate; nessuna è selezionata."""
        for old_button in self.platform_buttons.buttons():
            self.platform_buttons.removeButton(old_button)
            self.platform_pills.removeWidget(old_button)
            old_button.hide()
            old_button.deleteLater()
        for platform in platforms:
            button = create_pill(platform)
            self.platform_buttons.addButton(button)
            self.platform_pills.addWidget(button)

    def selected_platform(self) -> str:
        """Restituisce la piattaforma della pillola scelta, oppure quella scritta nel campo."""
        checked_button = self.platform_buttons.checkedButton()
        if checked_button is not None:
            return checked_button.text()
        return self.platform_input.text().strip()

    def selected_status(self) -> str:
        """Restituisce lo stato scelto, come valore interno ("playing", "completed"...)."""
        return STATUS_CHOICES[self.status_buttons.checkedId()][0]

    def update_visible_fields(self) -> None:
        """Mostra la data di completamento solo per una partita completata."""
        completed = self.selected_status() == "completed"
        self.completion_caption.setVisible(completed)
        self.completion_date_input.setVisible(completed)

    def submit(self) -> None:
        """Consegna la partita se i dati sono validi, altrimenti mostra il primo errore."""
        platform = self.selected_platform()
        start_date = self.start_date_input.date().toString(ISO_FORMAT)
        completion_date = None
        if self.selected_status() == "completed":
            completion_date = self.completion_date_input.date().toString(ISO_FORMAT)
        error = "Indica la piattaforma su cui giochi." if platform == "" else None
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


def create_caption(text: str) -> QLabel:
    """Restituisce la piccola etichetta sopra un campo."""
    caption = QLabel(text)
    caption.setObjectName("fieldCaption")
    return caption


def create_pill(text: str) -> QPushButton:
    """Restituisce un bottone a pillola selezionabile."""
    button = QPushButton(text)
    button.setObjectName("pillButton")
    button.setCheckable(True)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button
