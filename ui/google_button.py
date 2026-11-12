"""Bottone "Accedi con Google" secondo le regole di Google (branding guidelines di Sign in with Google).

Tema scuro: sfondo #131314, bordo #8E918F, testo #E3E3E3 in Google Sans Medium 14 (i colori sono in style.qss).
Il logo è la "G" ufficiale, ritagliata dal PNG @4x del pacchetto signin-assets di Google senza modifiche
(con il suo sfondo #131314, uguale a quello del bottone), con 12px a sinistra e 10px a destra.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ui.theme import ICONS_DIR

GOOGLE_LOGO_FILE = ICONS_DIR / "google-g.png"
BUTTON_HEIGHT = 40
LOGO_SIZE = 20
LOGO_LEFT_PADDING = 12
LOGO_RIGHT_PADDING = 10
TEXT_RIGHT_PADDING = 12


class GoogleButton(QPushButton):
    """Bottone a pillola con la "G" di Google e il testo; logo e testo stanno al centro, insieme."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("googleButton")
        self.setFixedHeight(BUTTON_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.logo = QLabel()
        self.logo.setFixedSize(LOGO_SIZE, LOGO_SIZE)
        self.logo.setPixmap(self.logo_pixmap())
        self.text_label = QLabel(text)
        self.text_label.setObjectName("googleButtonText")
        for label in (self.logo, self.text_label):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(LOGO_LEFT_PADDING, 0, TEXT_RIGHT_PADDING, 0)
        layout.setSpacing(LOGO_RIGHT_PADDING)
        layout.addStretch()
        layout.addWidget(self.logo)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def set_label(self, text: str) -> None:
        """Cambia il testo mostrato accanto al logo."""
        self.text_label.setText(text)

    def logo_pixmap(self) -> QPixmap:
        """Disegna la "G" alla risoluzione giusta per lo schermo (nitida anche con lo zoom di Windows)."""
        ratio = self.devicePixelRatioF()
        side = round(LOGO_SIZE * ratio)
        pixmap = QPixmap(str(GOOGLE_LOGO_FILE)).scaled(
            side, side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        pixmap.setDevicePixelRatio(ratio)
        return pixmap
