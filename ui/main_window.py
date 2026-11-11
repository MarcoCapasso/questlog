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
    QFrame,
)

from core.repository import GameRepository
from ui.library_page import LibraryPage


class MainWindow(QMainWindow):
    """La finestra principale: barra di navigazione in alto e pagine sotto."""

    def __init__(self, repository: GameRepository) -> None:
        super().__init__()
        self.setWindowTitle("Questlog")
        screen_area = self.screen().availableGeometry()
        self.resize(int(screen_area.width() * 0.7), int(screen_area.height() * 0.75))
        self.setMinimumSize(960, 600)

        self.pages = QStackedWidget()
        self.nav_buttons = QButtonGroup(self)
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 14, 40, 14)
        header_layout.setSpacing(6)
        logo = QLabel("QUESTLOG")
        logo.setObjectName("logo")
        header_layout.addWidget(logo)

        pages = [
            ("Home", create_placeholder_page("Home")),
            ("Libreria", LibraryPage(repository)),
            ("Statistiche", create_placeholder_page("Statistiche")),
        ]
        for index, (name, page) in enumerate(pages):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setCheckable(True)
            self.nav_buttons.addButton(button, index)
            header_layout.addWidget(button)
            self.pages.addWidget(page)
        header_layout.addStretch()

        self.nav_buttons.idClicked.connect(self.pages.setCurrentIndex)
        self.nav_buttons.button(0).setChecked(True)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(header)
        central_layout.addWidget(self.pages)
        self.setCentralWidget(central)


def create_placeholder_page(title: str) -> QWidget:
    """Restituisce una pagina provvisoria che mostra solo il proprio titolo."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(40, 28, 40, 28)
    layout.addWidget(QLabel(title))
    layout.addStretch()
    return page