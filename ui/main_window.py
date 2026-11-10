"""Finestra principale di Questlog."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

PAGE_NAMES = ["Home", "Libreria", "Statistiche",]


class MainWindow(QMainWindow):
    """La finestra principale: barra di navigazione in alto e pagine sotto."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Questlog")
        self.resize(1280, 820)

        self.pages = QStackedWidget()
        self.nav_buttons = QButtonGroup(self)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.addWidget(QLabel("QUESTLOG"))

        for index, name in enumerate(PAGE_NAMES):
            button = QPushButton(name)
            button.setCheckable(True)
            self.nav_buttons.addButton(button, index)
            header_layout.addWidget(button)
            self.pages.addWidget(create_placeholder_page(name))
        header_layout.addStretch()

        self.nav_buttons.idClicked.connect(self.pages.setCurrentIndex)
        self.nav_buttons.button(0).setChecked(True)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(header)
        central_layout.addWidget(self.pages)
        self.setCentralWidget(central)


def create_placeholder_page(title: str) -> QWidget:
    """Restituisce una pagina provvisoria che mostra solo il proprio titolo."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(title))
    layout.addStretch()
    return page