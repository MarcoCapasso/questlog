"""Grafici delle statistiche della libreria, salvati come immagini."""

import matplotlib.pyplot as plt
import pandas as pd

PLATFORM_CHART_FILE = "chart_hours_by_platform.png"


def save_hours_by_platform_chart(hours_by_platform: pd.Series) -> None:
    """Salva un grafico a barre con le ore giocate su ogni piattaforma."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(hours_by_platform.index, hours_by_platform.to_numpy())
    ax.set_title("Ore giocate per piattaforma")
    ax.set_xlabel("Piattaforma")
    ax.set_ylabel("Ore")
    fig.tight_layout()
    fig.savefig(PLATFORM_CHART_FILE)
    plt.close(fig)