"""Widget di base riutilizzati in più pagine."""

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QToolButton, QWidget

from ui.theme import ICONS_DIR

TEXT_MARGIN = 12
MAX_RATING = 10
STAR_SIZE = 24


class HoursSpinBox(QDoubleSpinBox):
    """Campo numerico per le ore, senza freccette e senza decimali inutili (12 invece di 12,0)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setTextMargins(TEXT_MARGIN, 0, 0, 0)

    def textFromValue(self, value: float) -> str:
        """Restituisce il numero senza zeri finali, con il separatore decimale della lingua di sistema."""
        return self.locale().toString(value, "g", 12)


class RatingInput(QWidget):
    """Dieci stelle cliccabili: la stella scelta e quelle prima si colorano; un secondo click toglie il voto."""

    rating_changed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rating: int | None = None
        self.empty_star = QIcon(str(ICONS_DIR / "star-empty.svg"))
        self.full_star = QIcon(str(ICONS_DIR / "star-full.svg"))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.stars: list[QToolButton] = []
        for value in range(1, MAX_RATING + 1):
            star = QToolButton()
            star.setObjectName("ratingStar")
            star.setIconSize(QSize(STAR_SIZE, STAR_SIZE))
            star.setToolTip(f"{value} su {MAX_RATING}")
            star.clicked.connect(lambda _checked=False, chosen=value: self.choose(chosen))
            self.stars.append(star)
            layout.addWidget(star)

        self.value_label = QLabel()
        self.value_label.setObjectName("ratingValue")
        layout.addSpacing(10)
        layout.addWidget(self.value_label)
        layout.addStretch()
        self.set_rating(None)

    def choose(self, value: int) -> None:
        """Imposta il voto cliccato, oppure lo toglie se era già quello scelto, e avvisa con rating_changed."""
        self.set_rating(None if value == self.rating else value)
        self.rating_changed.emit(self.rating)

    def set_rating(self, rating: int | None) -> None:
        """Imposta il voto (None = nessun voto) e aggiorna le stelle."""
        self.rating = rating
        for value, star in enumerate(self.stars, start=1):
            filled = rating is not None and value <= rating
            star.setIcon(self.full_star if filled else self.empty_star)
        self.value_label.setText("Nessun voto" if rating is None else f"{rating}/{MAX_RATING}")
