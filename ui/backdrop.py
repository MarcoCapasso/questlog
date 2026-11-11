"""Sfondo della pagina del gioco: un'immagine del gioco, trasparente e sfumata verso il colore della pagina."""

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget

from ui.covers import cover_loader

PAGE_COLOR = QColor("#101214")
BACKDROP_HEIGHT = 560
BACKDROP_OPACITY = 0.3


class BackdropWidget(QWidget):
    """Contenitore che disegna dietro ai propri figli l'immagine di sfondo del gioco."""

    def __init__(self) -> None:
        super().__init__()
        self.url: str | None = None
        self.pixmap: QPixmap | None = None
        cover_loader().loaded.connect(self.on_image_loaded)

    def set_url(self, url: str | None) -> None:
        """Cambia l'immagine di sfondo; None la toglie."""
        self.url = url
        self.pixmap = cover_loader().request(url) if url is not None else None
        self.update()

    def on_image_loaded(self, url: str, pixmap: QPixmap) -> None:
        """Usa l'immagine appena scaricata, se è quella dello sfondo attuale."""
        if url == self.url:
            self.pixmap = pixmap
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Riempie di colore la pagina e, in alto, disegna l'immagine trasparente con una sfumatura verso il basso."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), PAGE_COLOR)
        if self.pixmap is None:
            return
        target = QRectF(0, 0, self.width(), min(self.height(), BACKDROP_HEIGHT))
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(BACKDROP_OPACITY)
        painter.drawPixmap(target, self.pixmap, crop_to_fill(self.pixmap, target))
        painter.setOpacity(1)

        fade = QLinearGradient(0, 0, 0, target.height())
        fade.setColorAt(0, QColor(16, 18, 20, 60))
        fade.setColorAt(1, PAGE_COLOR)
        painter.fillRect(target, fade)


def crop_to_fill(pixmap: QPixmap, target: QRectF) -> QRectF:
    """Restituisce la parte centrale dell'immagine con le proporzioni di target, così la riempie senza deformarla."""
    target_ratio = target.width() / target.height()
    width = float(pixmap.width())
    height = float(pixmap.height())
    if width / height > target_ratio:
        crop_width = height * target_ratio
        return QRectF((width - crop_width) / 2, 0, crop_width, height)
    crop_height = width / target_ratio
    return QRectF(0, (height - crop_height) / 4, width, crop_height)
