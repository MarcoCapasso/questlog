"""Pagina Impostazioni: mostra lo stato dei servizi collegati e dove sono salvati i dati."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from core.storage import LIBRARY_FILE

PAGE_MARGIN = 40
PANEL_WIDTH = 680


class SettingsPage(QWidget):
    """Impostazioni di Questlog: account, catalogo, traduzioni e posizione dei dati."""

    def __init__(self, catalog_is_demo: bool, translation_enabled: bool, cloud_enabled: bool) -> None:
        super().__init__()
        heading = QLabel("Impostazioni")
        heading.setObjectName("pageTitle")

        catalog_text = (
            "Catalogo di prova: aggiungi IGDB_CLIENT_ID e IGDB_CLIENT_SECRET nel file .env "
            "per cercare tutti i giochi."
            if catalog_is_demo
            else "Collegato: ricerca, copertine e screenshot arrivano da IGDB."
        )
        translation_text = (
            "Attive con DeepL: le descrizioni dei giochi sono in italiano."
            if translation_enabled
            else "Non attive: le descrizioni restano in inglese. Aggiungi DEEPL_API_KEY nel file .env per tradurle."
        )
        account_text = (
            "Accedi con Google o con email e password: la libreria è salvata online nel tuo account, "
            "e la ritrovi su ogni computer."
            if cloud_enabled
            else "Account non configurato: aggiungi SUPABASE_URL e SUPABASE_ANON_KEY nel file .env per salvare "
            "la libreria online."
        )
        data_text = (
            "La libreria è salvata nel database Supabase del tuo account: ogni utente vede solo i propri giochi."
            if cloud_enabled
            else f"La libreria è salvata in {LIBRARY_FILE.resolve()}"
        )
        sections = [
            ("Account", account_text),
            ("Catalogo IGDB", catalog_text),
            ("Traduzioni", translation_text),
            ("Dove sono i tuoi dati", data_text),
        ]

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(PAGE_MARGIN, 28, PAGE_MARGIN, PAGE_MARGIN)
        content_layout.setSpacing(16)
        content_layout.addWidget(heading)
        content_layout.addSpacing(8)
        for title, text in sections:
            content_layout.addWidget(create_section(title, text))
        content_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)


def create_section(title: str, text: str) -> QFrame:
    """Restituisce un riquadro con titolo e testo."""
    section = QFrame()
    section.setObjectName("formPanel")
    section.setMaximumWidth(PANEL_WIDTH)
    title_label = QLabel(title)
    title_label.setObjectName("formTitle")
    text_label = QLabel(text)
    text_label.setObjectName("gameMeta")
    text_label.setWordWrap(True)
    text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    layout = QVBoxLayout(section)
    layout.setContentsMargins(24, 20, 24, 22)
    layout.setSpacing(8)
    layout.addWidget(title_label)
    layout.addWidget(text_label)
    return section
