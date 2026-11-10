"""Finestra principale di Questlog."""

from PySide6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    """La finestra principale dell'applicazione."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Questlog")
        self.resize(1280, 820)