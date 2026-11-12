"""Carosello delle immagini di un gioco: un'immagine grande con le frecce e, sotto, le miniature."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.covers import CoverLabel
from ui.theme import ICONS_DIR

ARROW_SIZE = 40
ARROW_MARGIN = 12
THUMBNAIL_SIZE = QSize(128, 72)
DIMMED_OPACITY = 0.45


class Thumbnail(CoverLabel):
    """Miniatura cliccabile: è attenuata finché non è quella scelta."""

    clicked = Signal()

    def __init__(self, url: str) -> None:
        super().__init__(url, THUMBNAIL_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        """Mostra la miniatura piena se è scelta, attenuata altrimenti."""
        self.opacity.setOpacity(1 if selected else DIMMED_OPACITY)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Un click sinistro sulla miniatura emette clicked."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class ImageCarousel(QWidget):
    """Mostra una serie di immagini una alla volta; si cambia con le frecce o cliccando una miniatura."""

    def __init__(self, width: int) -> None:
        super().__init__()
        self.urls: list[str] = []
        self.thumbnails: list[Thumbnail] = []
        self.index = 0

        image_size = QSize(width, width * 9 // 16)
        self.main_image = CoverLabel(None, image_size)
        self.previous_button = create_arrow_button("chevron-left.svg", self.main_image)
        self.previous_button.move(ARROW_MARGIN, (image_size.height() - ARROW_SIZE) // 2)
        self.previous_button.clicked.connect(lambda: self.show_image(self.index - 1))
        self.next_button = create_arrow_button("chevron-right.svg", self.main_image)
        self.next_button.move(image_size.width() - ARROW_SIZE - ARROW_MARGIN, (image_size.height() - ARROW_SIZE) // 2)
        self.next_button.clicked.connect(lambda: self.show_image(self.index + 1))

        self.counter = QLabel(self.main_image)
        self.counter.setObjectName("carouselCounter")

        self.thumbnail_row = QHBoxLayout()
        self.thumbnail_row.setContentsMargins(0, 0, 0, 0)
        self.thumbnail_row.setSpacing(8)
        thumbnail_strip = QWidget()
        strip_layout = QHBoxLayout(thumbnail_strip)
        strip_layout.setContentsMargins(0, 0, 0, 0)
        strip_layout.addLayout(self.thumbnail_row)
        strip_layout.addStretch()
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_scroll.setWidget(thumbnail_strip)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumbnail_scroll.setFixedSize(width, THUMBNAIL_SIZE.height() + 14)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.main_image)
        layout.addWidget(self.thumbnail_scroll)

    def set_images(self, urls: list[str]) -> None:
        """Sostituisce le immagini del carosello e mostra la prima; senza immagini il carosello si nasconde."""
        for thumbnail in self.thumbnails:
            self.thumbnail_row.removeWidget(thumbnail)
            thumbnail.hide()
            thumbnail.deleteLater()
        self.urls = urls
        self.thumbnails = []
        for position, url in enumerate(urls):
            thumbnail = Thumbnail(url)
            thumbnail.clicked.connect(lambda chosen=position: self.show_image(chosen))
            self.thumbnail_row.addWidget(thumbnail)
            self.thumbnails.append(thumbnail)
        self.setVisible(bool(urls))
        many_images = len(urls) > 1
        self.previous_button.setVisible(many_images)
        self.next_button.setVisible(many_images)
        self.thumbnail_scroll.setVisible(many_images)
        if urls:
            self.show_image(0)

    def show_image(self, index: int) -> None:
        """Mostra l'immagine in quella posizione; dall'ultima si riparte dalla prima e viceversa."""
        self.index = index % len(self.urls)
        self.main_image.set_url(self.urls[self.index])
        for position, thumbnail in enumerate(self.thumbnails):
            thumbnail.set_selected(position == self.index)
        if self.thumbnails:
            self.thumbnail_scroll.ensureWidgetVisible(self.thumbnails[self.index])
        self.counter.setText(f"{self.index + 1} / {len(self.urls)}")
        self.counter.adjustSize()
        self.counter.move(
            self.main_image.width() - self.counter.width() - ARROW_MARGIN,
            self.main_image.height() - self.counter.height() - ARROW_MARGIN,
        )


def create_arrow_button(icon_name: str, parent: QWidget) -> QToolButton:
    """Restituisce un bottone rotondo con una freccia, posato sopra l'immagine."""
    button = QToolButton(parent)
    button.setObjectName("carouselArrow")
    button.setIcon(QIcon(str(ICONS_DIR / icon_name)))
    button.setIconSize(QSize(20, 20))
    button.setFixedSize(ARROW_SIZE, ARROW_SIZE)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button
