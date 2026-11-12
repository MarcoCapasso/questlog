"""Formattazione dei numeri per l'interfaccia, all'italiana."""

from core.analysis import LibrarySummary


def format_summary(summary: LibrarySummary) -> str:
    """Restituisce la riga dei numeri della libreria, con i valori in grassetto (testo HTML)."""
    parts = [
        f"{bold(format_number(summary.total_hours))} ore giocate",
        f"{bold(str(summary.completed_playthroughs))} partite completate",
    ]
    if summary.completion_rate is not None:
        parts.append(f"{bold(f'{summary.completion_rate:.0%}')} portate a termine")
    if summary.average_rating is not None:
        parts.append(f"voto medio {bold(format_number(summary.average_rating, decimals=1))} ★")
    if summary.median_days_to_complete is not None:
        parts.append(f"un gioco ti dura in media {bold(format_number(summary.median_days_to_complete))} giorni")
    return " &nbsp;·&nbsp; ".join(parts)


def bold(text: str) -> str:
    """Restituisce il testo in grassetto e in chiaro, come HTML."""
    return f'<b style="color:#F1F3F5">{text}</b>'


def format_number(value: float, decimals: int = 0) -> str:
    """Formatta un numero all'italiana: punto per le migliaia, virgola per i decimali (2.473 · 4,5).

    Un numero intero non mostra decimali anche se richiesti (4 e non 4,0).
    """
    if float(value).is_integer():
        decimals = 0
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")
