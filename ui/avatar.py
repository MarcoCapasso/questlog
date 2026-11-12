"""Avatar in alto a destra con il menu del profilo: accesso, impostazioni, dati e uscita dall'account."""

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QToolButton, QWidget

from core.cloud import CloudUser
from ui.covers import cover_loader, rounded_pixmap
from ui.theme import ICONS_DIR

AVATAR_SIZE = 40
PICTURE_SIZE = AVATAR_SIZE - 2
DEFAULT_ICON_SIZE = 22
INITIAL_BACKGROUND = "#3A4553"
INITIAL_COLOR = "#F1F3F5"
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
        self.setToolTip("Profilo")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.picture_url: str | None = None
        cover_loader().loaded.connect(self.on_picture_loaded)

        self.login_available = False
        self.profile_menu = QMenu(self)
        self.account_action = self.profile_menu.addAction("")
        self.account_action.setEnabled(False)
        self.login_action = self.profile_menu.addAction("Accedi o registrati", self.login_requested.emit)
        self.account_separator = self.profile_menu.addSeparator()
        self.profile_menu.addAction("Impostazioni", self.settings_requested.emit)
        self.data_action = self.profile_menu.addAction("Importa ed esporta", self.data_requested.emit)
        self.fullscreen_action = self.profile_menu.addAction("Schermo intero")
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        self.logout_separator = self.profile_menu.addSeparator()
        self.logout_action = self.profile_menu.addAction("Esci", self.logout_requested.emit)
        self.set_user(None)
        self.clicked.connect(self.show_menu)

    def set_login_available(self, available: bool) -> None:
        """Indica se Supabase è configurato: senza, la voce "Accedi" non compare."""
        self.login_available = available
        self.set_user(None)

    def set_user(self, user: CloudUser | None) -> None:
        """Aggiorna il menu: nome ed "Esci" con un utente, "Accedi o registrati" senza.

        Senza login non c'è una libreria, quindi sparisce anche "Importa ed esporta" (se l'account è previsto).
        """
        logged_in = user is not None
        self.account_action.setText(f"{user.name} · {user.email}" if user is not None else "")
        self.account_action.setVisible(logged_in)
        self.login_action.setVisible(not logged_in and self.login_available)
        self.account_separator.setVisible(logged_in or self.login_available)
        self.logout_separator.setVisible(logged_in)
        self.logout_action.setVisible(logged_in)
        self.data_action.setVisible(logged_in or not self.login_available)
        self.setToolTip(user.name if user is not None else "Profilo")
        self.show_picture(user)

    def show_picture(self, user: CloudUser | None) -> None:
        """Nel cerchio: la foto di Google se c'è, altrimenti l'iniziale del nome; senza login l'icona generica.

        La foto si scarica con lo stesso sistema delle copertine: compare l'iniziale e poi, appena arriva, la foto.
        """
        self.picture_url = user.avatar_url if user is not None else None
        if user is None:
            self.setIcon(QIcon(str(ICONS_DIR / "user.svg")))
            self.setIconSize(QSize(DEFAULT_ICON_SIZE, DEFAULT_ICON_SIZE))
            return
        self.setIconSize(QSize(PICTURE_SIZE, PICTURE_SIZE))
        self.setIcon(QIcon(self.initial_pixmap(user.name)))
        if self.picture_url is not None:
            picture = cover_loader().request(self.picture_url)
            if picture is not None:
                self.on_picture_loaded(self.picture_url, picture)

    def on_picture_loaded(self, url: str, picture: QPixmap) -> None:
        """Mostra la foto appena scaricata, ritagliata a cerchio, se è ancora quella dell'utente."""
        if url != self.picture_url:
            return
        size = QSize(PICTURE_SIZE, PICTURE_SIZE)
        self.setIcon(QIcon(rounded_pixmap(picture, size, PICTURE_SIZE // 2, self.devicePixelRatioF())))

    def initial_pixmap(self, name: str) -> QPixmap:
        """Disegna un cerchio con l'iniziale del nome, alla risoluzione giusta per lo schermo."""
        ratio = self.devicePixelRatioF()
        pixmap = QPixmap(round(PICTURE_SIZE * ratio), round(PICTURE_SIZE * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(INITIAL_BACKGROUND))
        area = QRectF(0, 0, PICTURE_SIZE, PICTURE_SIZE)
        painter.drawEllipse(area)
        font = QFont(self.font())
        font.setPixelSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(INITIAL_COLOR))
        painter.drawText(area, Qt.AlignmentFlag.AlignCenter, name[:1].upper() or "?")
        painter.end()
        return pixmap

    def show_menu(self) -> None:
        """Apre il menu sotto l'avatar, con il bordo destro allineato al suo, così non esce dalla finestra."""
        menu_width = self.profile_menu.sizeHint().width()
        position = self.mapToGlobal(QPoint(self.width() - menu_width, self.height() + MENU_GAP))
        self.profile_menu.popup(position)
