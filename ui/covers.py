"""Copertine dei giochi: scaricate da internet una volta sola, poi lette dalla cache su disco."""

from PySide6.QtCore import QObject, QRectF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkDiskCache, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QLabel, QWidget

from core.storage import DATA_DIR

CACHE_DIR = DATA_DIR / "cache" / "covers"
COVER_RADIUS = 8


class CoverLoader(QObject):
    """Scarica le copertine in modo asincrono e avvisa con il segnale loaded(url, immagine)."""

    loaded = Signal(str, QPixmap)

    def __init__(self) -> None:
        super().__init__()
        self.network = QNetworkAccessManager(self)
        disk_cache = QNetworkDiskCache(self)
        disk_cache.setCacheDirectory(str(CACHE_DIR))
        self.network.setCache(disk_cache)
        self.pixmaps: dict[str, QPixmap] = {}
        self.downloading: set[str] = set()

    def request(self, url: str) -> QPixmap | None:
        """Restituisce subito la copertina se è già in memoria; altrimenti la scarica ed emetterà loaded."""
        if url in self.pixmaps:
            return self.pixmaps[url]
        if url not in self.downloading:
            self.downloading.add(url)
            request = QNetworkRequest(QUrl(url))
            request.setAttribute(
                QNetworkRequest.Attribute.CacheLoadControlAttribute,
                QNetworkRequest.CacheLoadControl.PreferCache,
            )
            reply = self.network.get(request)
            reply.finished.connect(lambda: self.handle_reply(url, reply))
        return None

    def handle_reply(self, url: str, reply: QNetworkReply) -> None:
        """Legge l'immagine scaricata, la tiene in memoria e avvisa chi la aspetta."""
        self.downloading.discard(url)
        pixmap = QPixmap()
        if reply.error() == QNetworkReply.NetworkError.NoError and pixmap.loadFromData(reply.readAll()):
            self.pixmaps[url] = pixmap
            self.loaded.emit(url, pixmap)
        reply.deleteLater()


shared_loader: CoverLoader | None = None


def cover_loader() -> CoverLoader:
    """Restituisce l'unico CoverLoader dell'app, creandolo al primo utilizzo."""
    global shared_loader
    if shared_loader is None:
        shared_loader = CoverLoader()
    return shared_loader


class CoverLabel(QLabel):
    """Riquadro della copertina: grigio finché l'immagine non arriva, poi la mostra con gli angoli arrotondati."""

    def __init__(self, url: str | None, size: QSize, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("cover")
        self.setFixedSize(size)
        self.url = url
        if url is None:
            return
        loader = cover_loader()
        pixmap = loader.request(url)
        if pixmap is not None:
            self.show_cover(pixmap)
        else:
            loader.loaded.connect(self.on_cover_loaded)

    def on_cover_loaded(self, url: str, pixmap: QPixmap) -> None:
        """Mostra la copertina appena scaricata, se è quella di questo riquadro."""
        if url == self.url:
            self.show_cover(pixmap)

    def show_cover(self, pixmap: QPixmap) -> None:
        """Ritaglia l'immagine alle dimensioni del riquadro e la disegna con gli angoli arrotondati."""
        self.setPixmap(rounded_pixmap(pixmap, self.size(), COVER_RADIUS, self.devicePixelRatioF()))


def rounded_pixmap(source: QPixmap, logical_size: QSize, radius: int, pixel_ratio: float) -> QPixmap:
    """Restituisce l'immagine riempita e centrata nelle dimensioni date, con gli angoli arrotondati.

    pixel_ratio è il ridimensionamento dello schermo di Windows (per esempio 1.5 al 150%):
    l'immagine viene disegnata con più pixel, così resta nitida.
    """
    size = logical_size * pixel_ratio
    radius = round(radius * pixel_ratio)
    scaled = source.scaled(
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    left = (scaled.width() - size.width()) // 2
    top = (scaled.height() - size.height()) // 2

    result = QPixmap(size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size.width(), size.height()), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled, left, top, size.width(), size.height())
    painter.end()
    result.setDevicePixelRatio(pixel_ratio)
    return result
