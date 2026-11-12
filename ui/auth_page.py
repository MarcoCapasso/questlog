"""Pagina Accedi / Registrati: Google oppure email e password, con la conferma dell'email tramite link."""

from collections.abc import Callable
from typing import Literal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.cloud import CANCELLED_MESSAGE, MIN_PASSWORD_LENGTH, AuthService, CloudUser, validate_credentials
from ui.google_button import GoogleButton
from ui.tasks import run_in_background

Mode = Literal["sign_in", "sign_up", "confirm"]
PANEL_WIDTH = 400

TITLES = {
    "sign_in": ("Accedi a Questlog", "La tua libreria, su tutti i tuoi computer."),
    "sign_up": ("Crea il tuo account", "Bastano un'email e una password."),
    "confirm": ("Conferma la tua email", ""),
}
SUBMIT_TEXTS = {"sign_in": "Accedi", "sign_up": "Registrati", "confirm": ""}
SWITCH_TEXTS = {
    "sign_in": "Non hai un account? Registrati",
    "sign_up": "Hai già un account? Accedi",
    "confirm": "Torna all'accesso",
}
GOOGLE_TEXTS = {"sign_in": "Accedi con Google", "sign_up": "Registrati con Google", "confirm": ""}


class AuthPage(QWidget):
    """Accesso e registrazione: emette signed_in con l'utente quando si è dentro.

    Dopo la registrazione la pagina aspetta il clic sul link di conferma arrivato per email:
    il link riporta su localhost, l'app lo riceve e si entra da soli, senza scrivere niente.
    """

    signed_in = Signal(object)

    def __init__(self, auth: AuthService) -> None:
        super().__init__()
        self.auth = auth
        self.mode: Mode = "sign_in"
        self.waiting_for_link = False
        self.pending_email = ""
        self.pending_password = ""

        self.title = QLabel()
        self.title.setObjectName("authTitle")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("gameMeta")
        self.subtitle.setWordWrap(True)

        self.google_button = GoogleButton("")
        self.google_button.clicked.connect(self.start_google)
        self.divider = create_divider()

        self.email_input = create_input("nome@esempio.com")
        self.password_input = create_input("", password=True)
        self.confirmation_input = create_input("Scrivila di nuovo", password=True)
        self.email_field = create_field("Email", self.email_input)
        self.password_field = create_field("Password", self.password_input)
        self.confirmation_field = create_field("Ripeti la password", self.confirmation_input)
        for line_edit in (self.email_input, self.password_input, self.confirmation_input):
            line_edit.returnPressed.connect(self.submit)

        self.message = QLabel()
        self.message.setObjectName("authMessage")
        self.message.setWordWrap(True)
        self.submit_button = QPushButton()
        self.submit_button.setObjectName("primaryButton")
        self.submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_button.clicked.connect(self.submit)
        self.cancel_button = create_text_button("Annulla l'accesso con Google", self.auth.cancel_waiting)
        self.resend_button = create_text_button("Mandami un'altra email", self.resend_email)
        self.switch_button = create_text_button("", self.switch_mode)

        panel = QFrame()
        panel.setObjectName("formPanel")
        panel.setFixedWidth(PANEL_WIDTH)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(32, 30, 32, 26)
        panel_layout.setSpacing(14)
        panel_layout.addWidget(self.title)
        panel_layout.addWidget(self.subtitle)
        panel_layout.addSpacing(4)
        panel_layout.addWidget(self.google_button)
        panel_layout.addWidget(self.divider)
        for field in (self.email_field, self.password_field, self.confirmation_field):
            panel_layout.addWidget(field)
        panel_layout.addWidget(self.message)
        panel_layout.addWidget(self.submit_button)
        for button in (self.cancel_button, self.resend_button, self.switch_button):
            panel_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(panel)
        row.addStretch()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 28, 40, 40)
        layout.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(2)
        self.start()

    def start(self) -> None:
        """Riparte da zero: modulo di accesso vuoto, senza messaggi e senza password ricordate."""
        for line_edit in (self.email_input, self.password_input, self.confirmation_input):
            line_edit.clear()
        self.pending_password = ""
        self.set_busy(False)
        self.set_mode("sign_in")

    def set_mode(self, mode: Mode, message: str = "") -> None:
        """Mostra i campi giusti per accesso, registrazione o attesa della conferma."""
        self.mode = mode
        title, subtitle = TITLES[mode]
        if mode == "confirm":
            subtitle = (
                f"Ti abbiamo mandato un link a {self.pending_email}. Aprilo su questo computer: "
                "appena lo clicchi, entri in Questlog."
            )
        self.title.setText(title)
        self.subtitle.setText(subtitle)
        self.google_button.set_label(GOOGLE_TEXTS[mode])
        self.submit_button.setText(SUBMIT_TEXTS[mode])
        self.switch_button.setText(SWITCH_TEXTS[mode])
        self.password_input.setPlaceholderText(f"Almeno {MIN_PASSWORD_LENGTH} caratteri" if mode == "sign_up" else "")

        entering = mode != "confirm"
        for widget in (self.google_button, self.divider, self.email_field, self.password_field, self.submit_button):
            widget.setVisible(entering)
        self.confirmation_field.setVisible(mode == "sign_up")
        self.resend_button.setVisible(not entering)
        self.show_message(message)
        if entering:
            self.email_input.setFocus()

    def switch_mode(self) -> None:
        """Passa da accesso a registrazione e viceversa; dall'attesa della conferma si torna all'accesso."""
        if self.mode == "confirm":
            self.stop_waiting()
        self.set_mode("sign_up" if self.mode == "sign_in" else "sign_in")

    def show_message(self, text: str, error: bool = False) -> None:
        """Mostra un messaggio sotto i campi (rosso se è un errore); con il testo vuoto lo nasconde."""
        self.message.setText(text)
        self.message.setProperty("error", error)
        self.message.style().unpolish(self.message)
        self.message.style().polish(self.message)
        self.message.setVisible(text != "")

    def show_error(self, message: str) -> None:
        """Una richiesta è fallita: si può riprovare."""
        self.set_busy(False)
        self.show_message(message, error=True)

    def set_busy(self, busy: bool, waiting_for_google: bool = False) -> None:
        """Durante una richiesta i bottoni si disattivano, così non parte due volte."""
        for button in (self.google_button, self.submit_button, self.resend_button, self.switch_button):
            button.setEnabled(not busy)
        self.cancel_button.setVisible(waiting_for_google)

    def submit(self) -> None:
        """Invio del modulo (bottone o tasto Invio): controlla i campi e manda la richiesta in background."""
        if self.mode == "confirm" or not self.submit_button.isEnabled():
            return
        email = self.email_input.text().strip()
        password = self.password_input.text()
        signing_up = self.mode == "sign_up"
        confirmation = self.confirmation_input.text() if signing_up else None
        problem = validate_credentials(email, password, confirmation)
        if problem is not None:
            self.show_message(problem, error=True)
            return

        self.pending_email = email
        self.pending_password = password
        self.set_busy(True)
        self.show_message("Un attimo…")
        if signing_up:
            run_in_background(lambda: self.auth.sign_up_with_email(email, password), self.on_email_sent, self.show_error)
        else:
            run_in_background(
                lambda: self.auth.sign_in_with_email(email, password), self.on_email_sign_in, self.show_error
            )

    def on_email_sign_in(self, user: CloudUser | None) -> None:
        """Accesso con email: se l'email non è ancora confermata, manda un nuovo link e lo aspetta."""
        if user is None:
            self.resend_email()
            return
        self.finish(user)

    def resend_email(self) -> None:
        """Manda (di nuovo) l'email di conferma: rifare la registrazione con gli stessi dati fa proprio questo."""
        self.set_busy(True)
        email, password = self.pending_email, self.pending_password
        run_in_background(lambda: self.auth.sign_up_with_email(email, password), self.on_email_sent, self.show_error)

    def on_email_sent(self, user: CloudUser | None) -> None:
        """L'email con il link è partita: si aspetta il clic (se Supabase non chiede conferma, si è già dentro)."""
        if user is not None:
            self.finish(user)
            return
        self.set_busy(False)
        self.set_mode("confirm", "In attesa del clic sul link…")
        if not self.waiting_for_link:
            self.waiting_for_link = True
            run_in_background(self.auth.wait_for_email_confirmation, self.on_link_clicked, self.on_waiting_failed)

    def on_link_clicked(self, user: CloudUser) -> None:
        """Il link è stato cliccato: l'account è confermato e si è dentro."""
        self.waiting_for_link = False
        self.finish(user)

    def on_waiting_failed(self, message: str) -> None:
        """L'attesa del link è finita senza clic: lo dice, a meno che non sia stata annullata apposta."""
        if message == CANCELLED_MESSAGE:
            return
        self.waiting_for_link = False
        self.show_message(f"{message} Se hai già cliccato il link, torna all'accesso ed entra con la password.", True)

    def stop_waiting(self) -> None:
        """Smette di aspettare il link (l'errore "annullato" che arriverà poi viene ignorato)."""
        if self.waiting_for_link:
            self.waiting_for_link = False
            self.auth.cancel_waiting()

    def finish(self, user: CloudUser) -> None:
        """Si è dentro: la pagina si ripulisce (niente password lasciate in giro) e avvisa la finestra."""
        self.start()
        self.signed_in.emit(user)

    def start_google(self) -> None:
        """Login con Google: si apre il browser e qui si aspetta, con la possibilità di annullare."""
        self.set_busy(True, waiting_for_google=True)
        self.show_message("Completa l'accesso nel browser…")
        run_in_background(self.auth.sign_in_with_google, self.finish, self.show_error)


def create_input(placeholder: str, password: bool = False) -> QLineEdit:
    """Restituisce un campo di testo del modulo; con password=True nasconde quello che scrivi."""
    line_edit = QLineEdit()
    line_edit.setObjectName("formInput")
    line_edit.setPlaceholderText(placeholder)
    if password:
        line_edit.setEchoMode(QLineEdit.EchoMode.Password)
    return line_edit


def create_field(caption: str, line_edit: QLineEdit) -> QWidget:
    """Restituisce l'etichetta con il suo campo, insieme, così si mostrano e nascondono in un colpo."""
    field = QWidget()
    caption_label = QLabel(caption)
    caption_label.setObjectName("fieldCaption")
    layout = QVBoxLayout(field)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    layout.addWidget(caption_label)
    layout.addWidget(line_edit)
    return field


def create_divider() -> QWidget:
    """Restituisce la riga "oppure" tra il bottone di Google e i campi email e password."""
    divider = QWidget()
    layout = QHBoxLayout(divider)
    layout.setContentsMargins(0, 4, 0, 4)
    layout.setSpacing(12)
    word = QLabel("oppure")
    word.setObjectName("fieldCaption")
    layout.addWidget(create_line(), 1)
    layout.addWidget(word)
    layout.addWidget(create_line(), 1)
    return divider


def create_line() -> QFrame:
    """Restituisce una linea orizzontale sottile."""
    line = QFrame()
    line.setObjectName("dividerLine")
    line.setFixedHeight(1)
    return line


def create_text_button(text: str, slot: Callable[[], None]) -> QPushButton:
    """Restituisce un bottone che sembra un link."""
    button = QPushButton(text)
    button.setObjectName("textButton")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.clicked.connect(slot)
    return button
