"""Grafici delle statistiche della libreria, salvati come immagini."""

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

PLATFORM_CHART_FILE = "chart_hours_by_platform.png"
STATUS_CHART_FILE = "chart_playthroughs_by_status.png"
COMPLETIONS_CHART_FILE = "chart_completions_per_year.png"
HOURS_HISTOGRAM_FILE = "chart_hours_per_game.png"


def save_hours_by_platform_chart(hours_by_platform: pd.Series) -> None:
    """Salva un grafico a barre con le ore giocate su ogni piattaforma."""
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(hours_by_platform.index, hours_by_platform.to_numpy())
    ax.bar_label(bars, fmt="%g")
    ax.set_title("Ore giocate per piattaforma")
    ax.set_xlabel("Piattaforma")
    ax.set_ylabel("Ore")
    fig.tight_layout()
    fig.savefig(PLATFORM_CHART_FILE)
    plt.close(fig)


def save_status_chart(status_counts: pd.Series) -> None:
    """Salva un grafico a barre con il numero di partite per ogni stato."""
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(status_counts.index, status_counts.to_numpy())
    ax.bar_label(bars)
    ax.set_title("Partite per stato")
    ax.set_xlabel("Stato")
    ax.set_ylabel("Partite")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()
    fig.savefig(STATUS_CHART_FILE)
    plt.close(fig)



def save_completions_chart(completions: pd.Series) -> None:
    """Salva un grafico a barre con il numero di partite completate in ogni anno."""
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(completions.index.astype(str), completions.to_numpy())
    ax.bar_label(bars)
    ax.set_title("Partite completate per anno")
    ax.set_xlabel("Anno")
    ax.set_ylabel("Partite")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()
    fig.savefig(COMPLETIONS_CHART_FILE)
    plt.close(fig)


def save_hours_histogram(hours_per_game: pd.Series, median_hours: float) -> None:
    """Salva un istogramma delle ore totali per gioco, con la mediana evidenziata."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(hours_per_game.to_numpy(), bins=10, edgecolor="white")
    ax.axvline(median_hours, color="black", linestyle="--", label=f"Mediana: {median_hours:g} ore")
    ax.legend()
    ax.set_title("Distribuzione delle ore per gioco")
    ax.set_xlabel("Ore totali")
    ax.set_ylabel("Giochi")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()
    fig.savefig(HOURS_HISTOGRAM_FILE)
    plt.close(fig)