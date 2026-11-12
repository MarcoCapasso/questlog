"""Avatar in alto a destra con il menu del profilo: accesso, impostazioni, dati e uscita dall'account."""

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QToolButton, QWidget

from core.cloud import CloudUser
from ui.theme import ICONS_DIR

AVATAR_SIZE = 40
MENU_GAP = 8


class AvatarButton(QToolButton):
    """Cerchio con l'icona del profilo; cliccandolo si apre il menu, allineato al suo bordo destro.

    Il menu cambia con l'accesso: "Accedi o registrati" quando sei fuori, nome ed "Esci" quando sei dentro.
    """

    settings_requested = Signal()
    data_requested = Signal()
    login_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("avatarButton")
        self.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.setIcon(QIcon(str(ICONS_DIR / "user.svg")))
        self.setIconSize(QSize(22, 22))
        self.setToolTip("Profilo")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.login_available = False
        self.profile_menu = QMenu(self)
        self.account_action = self.profile_menu.addAction("")
        self.account_action.setEnabled(False)
        self.login_action = self.profile_menu.addAction("Accedi o registrati", self.login_requested.emit)
        self.account_separator = self.profile_menu.addSeparator()
        self.profile_menu.addAction("Impostazioni", self.settings_requested.emit)
        self.profile_menu.addAction("Importa ed esporta", self.data_requested.emit)
        self.logout_separator = self.profile_menu.addSeparator()
        self.logout_action = self.profile_menu.addAction("Esci", self.logout_requested.emit)
        self.set_user(None)
        self.clicked.connect(self.show_menu)

    def set_login_available(self, available: bool) -> None:
        """Indica se Supabase è configurato: senza, la voce "Accedi" non compare."""
        self.login_available = available
        self.set_user(None)

    def set_user(self, user: CloudUser | None) -> None:
        """Aggiorna il menu: nome ed "Esci" con un utente, "Accedi o registrati" senza."""
        logged_in = user is not None
        self.account_action.setText(f"{user.name} · {user.email}" if user is not None else "")
        self.account_action.setVisible(logged_in)
        self.login_action.setVisible(not logged_in and self.login_available)
        self.account_separator.setVisible(logged_in or self.login_available)
        self.logout_separator.setVisible(logged_in)
        self.logout_action.setVisible(logged_in)
        self.setToolTip(user.name if user is not None else "Profilo")

    def show_menu(self) -> None:
        """Apre il menu sotto l'avatar, con il bordo destro allineato al suo, così non esce dalla finestra."""
        menu_width = self.profile_menu.sizeHint().width()
        position = self.mapToGlobal(QPoint(self.width() - menu_width, self.height() + MENU_GAP))
        self.profile_menu.popup(position)
