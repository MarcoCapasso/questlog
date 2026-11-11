"""Widget di base riutilizzati in più pagine: ore, date e voto."""

from PySide6.QtCore import QDate, QEvent, QObject, QRect, QRegularExpression, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QMouseEvent, QPainter, QRegularExpressionValidator, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QWidget,
)

from core.library import MAX_RATING
from ui.theme import ICONS_DIR

STAR_SIZE = 26
FIELD_HEIGHT = 40
FIELD_PADDING = 12
CURSOR_SPACE = 8
HOURS_PATTERN = r"\d{0,5}([.,]\d?)?"
DATE_FORMAT = "dd/MM/yyyy"
CALENDAR_SIZE = QSize(320, 300)
TEXT_COLOR = QColor("#F1F3F5")
MUTED_COLOR = QColor("#5A6169")
DISABLED_COLOR = QColor("#343A41")
SELECTED_TEXT_COLOR = QColor("#101214")
TODAY_COLOR = QColor("#8FE0A8")
CALENDAR_BACKGROUND = QColor("#1C2024")


class HoursInput(QFrame):
    """Campo per le ore: il numero si scrive da zero e "ore" resta fisso subito dopo, senza poterlo toccare."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("hoursInput")
        self.setFixedHeight(FIELD_HEIGHT)
        self.setCursor(Qt.CursorShape.IBeamCursor)

        self.number_input = QLineEdit()
        self.number_input.setObjectName("hoursNumber")
        self.number_input.setPlaceholderText("0")
        self.number_input.setValidator(QRegularExpressionValidator(QRegularExpression(HOURS_PATTERN)))
        self.number_input.textChanged.connect(self.fit_number_width)
        self.number_input.installEventFilter(self)

        unit = QLabel("ore")
        unit.setObjectName("hoursUnit")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(FIELD_PADDING, 0, FIELD_PADDING, 0)
        layout.setSpacing(4)
        layout.addWidget(self.number_input)
        layout.addWidget(unit)
        layout.addStretch()
        self.fit_number_width()

    def value(self) -> float:
        """Restituisce le ore scritte; con il campo vuoto (o solo una virgola) restituisce 0."""
        try:
            return float(self.number_input.text().replace(",", "."))
        except ValueError:
            return 0.0

    def set_value(self, hours: float) -> None:
        """Scrive le ore nel campo; con 0 lo svuota, così si vede lo 0 grigio da sovrascrivere."""
        self.number_input.setText("" if hours == 0 else f"{hours:g}".replace(".", ","))

    def fit_number_width(self) -> None:
        """Allarga il campo del numero quanto il testo, così "ore" lo segue sempre a un spazio di distanza."""
        text = self.number_input.text() or self.number_input.placeholderText()
        width = self.number_input.fontMetrics().horizontalAdvance(text) + CURSOR_SPACE
        self.number_input.setFixedWidth(width)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Un click in qualsiasi punto del riquadro porta il cursore alla fine del numero."""
        self.number_input.setFocus()
        self.number_input.end(False)
        super().mousePressEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Ricalcola la larghezza quando arriva il font del QSS; col focus evidenzia il bordo come negli altri campi."""
        if watched is self.number_input and event.type() in (QEvent.Type.Polish, QEvent.Type.FontChange):
            self.fit_number_width()
        if watched is self.number_input and event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            self.setProperty("focused", event.type() == QEvent.Type.FocusIn)
            self.style().unpolish(self)
            self.style().polish(self)
        return super().eventFilter(watched, event)


class Calendar(QCalendarWidget):
    """Calendario a tendina: settimana da lunedì, giorno scelto in un cerchio chiaro, oggi con un anello verde."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("calendar")
        self.setMinimumSize(CALENDAR_SIZE)
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)

        header_format = QTextCharFormat()
        header_format.setForeground(MUTED_COLOR)
        header_format.setFontWeight(QFont.Weight.DemiBold)
        header_format.setBackground(CALENDAR_BACKGROUND)
        self.setHeaderTextFormat(header_format)
        for day in (Qt.DayOfWeek.Saturday, Qt.DayOfWeek.Sunday):
            self.setWeekdayTextFormat(day, header_format)

    def paintCell(self, painter: QPainter, rect: QRect, date: QDate) -> None:
        """Disegna un giorno: numero centrato, cerchio pieno se scelto, anello se è oggi, grigio se non selezionabile."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(rect.width(), rect.height()) - 6
        circle = QRect(0, 0, side, side)
        circle.moveCenter(rect.center())

        selectable = self.minimumDate() <= date <= self.maximumDate()
        in_shown_month = date.month() == self.monthShown()
        text_color = TEXT_COLOR
        if not selectable:
            text_color = DISABLED_COLOR
        elif not in_shown_month:
            text_color = MUTED_COLOR

        if date == self.selectedDate():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(TEXT_COLOR)
            painter.drawEllipse(circle)
            text_color = SELECTED_TEXT_COLOR
        elif date == QDate.currentDate():
            painter.setPen(TODAY_COLOR)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(circle)

        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(date.day()))
        painter.restore()


class DateInput(QDateEdit):
    """Campo data in formato italiano con il calendario a tendina personalizzato."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDisplayFormat(DATE_FORMAT)
        self.setCalendarPopup(True)
        self.setCalendarWidget(Calendar())


class RatingInput(QWidget):
    """Cinque stelle cliccabili: la stella scelta e quelle prima si colorano; un secondo click toglie il voto."""

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
            star.setCursor(Qt.CursorShape.PointingHandCursor)
            star.clicked.connect(lambda _checked=False, chosen=value: self.choose(chosen))
            self.stars.append(star)
            layout.addWidget(star)
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
