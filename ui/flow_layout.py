"""Layout che dispone i widget in fila e va a capo quando finisce lo spazio, come le parole in un testo.

Va messo dentro un widget contenitore dedicato: è il contenitore che viene allungato quando servono più righe.
"""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget


class FlowLayout(QLayout):
    """Versione Python dell'esempio "Flow Layout" della documentazione di Qt."""

    def __init__(self, parent: QWidget | None = None, spacing: int = 8) -> None:
        super().__init__(parent)
        self.items: list[QLayoutItem] = []
        self.gap = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item: QLayoutItem) -> None:
        """Chiamato da Qt per ogni widget aggiunto con addWidget."""
        self.items.append(item)

    def count(self) -> int:
        """Restituisce quanti elementi contiene il layout."""
        return len(self.items)

    def itemAt(self, index: int) -> QLayoutItem | None:  # type: ignore[override]
        """Restituisce l'elemento in quella posizione, oppure None."""
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index: int) -> QLayoutItem | None:  # type: ignore[override]
        """Toglie dal layout l'elemento in quella posizione e lo restituisce."""
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self) -> Qt.Orientation:
        """Il layout non chiede spazio extra in nessuna direzione."""
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        """L'altezza dipende dalla larghezza: più è stretto, più righe servono."""
        return True

    def heightForWidth(self, width: int) -> int:
        """Restituisce l'altezza necessaria per quella larghezza, simulando la disposizione."""
        return self.arrange(QRect(0, 0, width, 0), move_widgets=False)

    def setGeometry(self, rect: QRect) -> None:
        """Chiamato da Qt quando il layout riceve il suo spazio: dispone i widget e adatta l'altezza del contenitore.

        Senza questo passaggio il contenitore resterebbe alto una sola riga
        e le righe successive finirebbero sopra i widget che stanno sotto.
        """
        super().setGeometry(rect)
        needed_height = self.arrange(rect, move_widgets=True)
        container = self.parentWidget()
        if container is not None and container.minimumHeight() != needed_height:
            container.setMinimumHeight(needed_height)

    def sizeHint(self) -> QSize:
        """Dimensione consigliata: quella minima."""
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        """Dimensione minima: deve entrare almeno l'elemento più grande."""
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        return size

    def arrange(self, rect: QRect, move_widgets: bool) -> int:
        """Mette gli elementi in fila andando a capo quando non c'è spazio; restituisce l'altezza usata."""
        x = rect.x()
        y = rect.y()
        row_height = 0
        for item in self.items:
            item_size = item.sizeHint()
            if x + item_size.width() > rect.right() + 1 and row_height > 0:
                x = rect.x()
                y += row_height + self.gap
                row_height = 0
            if move_widgets:
                item.setGeometry(QRect(QPoint(x, y), item_size))
            x += item_size.width() + self.gap
            row_height = max(row_height, item_size.height())
        return y + row_height - rect.y()
