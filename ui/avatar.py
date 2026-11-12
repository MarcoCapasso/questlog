"""Avatar in alto a destra con il menu del profilo: impostazioni, dati e (in futuro) uscita dall'account."""

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QToolButton, QWidget

from ui.theme import ICONS_DIR

AVATAR_SIZE = 40
MENU_GAP = 8


class AvatarButton(QToolButton):
    """Cerchio con l'icona del profilo; cliccandolo si apre il menu, allineato al suo bordo destro.

    La voce "Esci" esiste già ma è nascosta: diventerà visibile con l'accesso online (Fase 6).
    """

    settings_requested = Signal()
    data_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("avatarButton")
        self.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.setIcon(QIcon(str(ICONS_DIR / "user.svg")))
        self.setIconSize(QSize(22, 22))
        self.setToolTip("Profilo")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.profile_menu = QMenu(self)
        self.profile_menu.addAction("Impostazioni", self.settings_requested.emit)
        self.profile_menu.addAction("Importa ed esporta", self.data_requested.emit)
        self.logout_separator = self.profile_menu.addSeparator()
        self.logout_action = self.profile_menu.addAction("Esci", self.logout_requested.emit)
        self.set_logged_in(False)
        self.clicked.connect(self.show_menu)

    def set_logged_in(self, logged_in: bool) -> None:
        """Mostra "Esci" solo quando c'è un account da cui uscire."""
        self.logout_separator.setVisible(logged_in)
        self.logout_action.setVisible(logged_in)

    def show_menu(self) -> None:
        """Apre il menu sotto l'avatar, con il bordo destro allineato al suo, così non esce dalla finestra."""
        menu_width = self.profile_menu.sizeHint().width()
        position = self.mapToGlobal(QPoint(self.width() - menu_width, self.height() + MENU_GAP))
        self.profile_menu.popup(position)
