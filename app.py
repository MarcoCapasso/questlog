"""Punto di ingresso dell'app desktop di Questlog."""

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> None:
    """Crea l'applicazione, mostra la finestra principale e avvia il ciclo di eventi."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()