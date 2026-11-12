"""Grafici delle statistiche della libreria: si creano come Figure e si possono salvare o mostrare nell'app.

Le Figure si creano con matplotlib.figure.Figure e non con pyplot: pyplot tiene un elenco globale
di finestre aperte, utile negli script ma scomodo dentro un'app che ridisegna i grafici più volte.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from core.storage import DATA_DIR

PLATFORM_CHART_FILE = DATA_DIR / "chart_hours_by_platform.png"
STATUS_CHART_FILE = DATA_DIR / "chart_playthroughs_by_status.png"
COMPLETIONS_CHART_FILE = DATA_DIR / "chart_completions_per_year.png"
HOURS_HISTOGRAM_FILE = DATA_DIR / "chart_hours_per_game.png"
FIGURE_SIZE = (8, 5)

STATUS_NAMES = {
    "playing": "In corso",
    "completed": "Completate",
    "dropped": "Abbandonate",
}


@dataclass
class ChartTheme:
    """Colori dei grafici: tenerli insieme permette di creare altri temi senza toccare le funzioni."""
    background: str
    text: str
    muted_text: str
    grid: str
    bar: str
    highlight: str
    status_colors: dict[str, str] = field(default_factory=dict)


LIGHT_THEME = ChartTheme(
    background="#FFFFFF",
    text="#101214",
    muted_text="#5A6169",
    grid="#E3E6E9",
    bar="#3A5C86",
    highlight="#101214",
    status_colors={"playing": "#2E9E5B", "completed": "#3A5C86", "dropped": "#D9822B"},
)


def create_hours_by_platform_figure(hours_by_platform: pd.Series, theme: ChartTheme = LIGHT_THEME) -> Figure:
    """Restituisce un grafico a barre orizzontali con le ore per piattaforma, la più giocata in alto."""
    figure, axes = create_figure(theme, grid_axis="x")
    ordered = hours_by_platform.sort_values()
    bars = axes.barh(ordered.index, ordered.to_numpy(), color=theme.bar)
    axes.bar_label(bars, fmt="%g", padding=4, color=theme.text)
    axes.set_title("Ore giocate per piattaforma")
    axes.set_xlabel("Ore")
    axes.margins(x=0.15)
    return figure


def create_status_figure(status_counts: pd.Series, theme: ChartTheme = LIGHT_THEME) -> Figure:
    """Restituisce un grafico a barre con le partite per stato, ognuna nel colore del suo stato."""
    figure, axes = create_figure(theme)
    labels = [STATUS_NAMES.get(str(status), str(status)) for status in status_counts.index]
    colors = [theme.status_colors.get(str(status), theme.bar) for status in status_counts.index]
    bars = axes.bar(labels, status_counts.to_numpy(), color=colors)
    axes.bar_label(bars, padding=4, color=theme.text)
    axes.set_title("Partite per stato")
    axes.set_ylabel("Partite")
    axes.yaxis.set_major_locator(MaxNLocator(integer=True))
    axes.margins(y=0.15)
    return figure


def create_completions_figure(completions: pd.Series, theme: ChartTheme = LIGHT_THEME) -> Figure:
    """Restituisce un grafico a barre con le partite completate in ogni anno."""
    figure, axes = create_figure(theme)
    bars = axes.bar(completions.index.astype(str), completions.to_numpy(), color=theme.bar)
    axes.bar_label(bars, padding=4, color=theme.text)
    axes.set_title("Partite completate per anno")
    axes.set_ylabel("Partite")
    axes.yaxis.set_major_locator(MaxNLocator(integer=True))
    axes.margins(y=0.15)
    return figure


def create_hours_histogram_figure(
    hours_per_game: pd.Series,
    median_hours: float,
    theme: ChartTheme = LIGHT_THEME,
) -> Figure:
    """Restituisce un istogramma delle ore totali per gioco, con la mediana evidenziata."""
    figure, axes = create_figure(theme)
    axes.hist(hours_per_game.to_numpy(), bins=10, color=theme.bar, edgecolor=theme.background)
    axes.axvline(median_hours, color=theme.highlight, linestyle="--", label=f"Mediana: {median_hours:g} ore".replace(".", ","))
    legend = axes.legend(facecolor=theme.background, edgecolor=theme.grid)
    for text in legend.get_texts():
        text.set_color(theme.text)
    axes.set_title("Distribuzione delle ore per gioco")
    axes.set_xlabel("Ore totali")
    axes.set_ylabel("Giochi")
    axes.yaxis.set_major_locator(MaxNLocator(integer=True))
    return figure


def create_figure(theme: ChartTheme, grid_axis: Literal["x", "y"] = "y") -> tuple[Figure, Axes]:
    """Restituisce una Figure con un solo grafico, già colorata secondo il tema.

    layout="constrained" ricalcola i margini a ogni disegno: quando nell'app il grafico
    cambia dimensione, le etichette lunghe (come "Nintendo Switch 2") non vengono tagliate.
    La griglia si disegna solo lungo l'asse dei valori (grid_axis), per non riempire il grafico di righe.
    """
    figure = Figure(figsize=FIGURE_SIZE, facecolor=theme.background, layout="constrained")
    axes = figure.add_subplot()
    axes.set_facecolor(theme.background)
    axes.title.set_color(theme.text)
    axes.title.set_fontweight("bold")
    axes.xaxis.label.set_color(theme.muted_text)
    axes.yaxis.label.set_color(theme.muted_text)
    axes.tick_params(colors=theme.muted_text)
    for side, spine in axes.spines.items():
        spine.set_visible(side in ("left", "bottom"))
        spine.set_color(theme.grid)
    axes.grid(axis=grid_axis, color=theme.grid, linewidth=0.8)
    axes.set_axisbelow(True)
    return figure, axes


def save_figure(figure: Figure, chart_file: Path) -> None:
    """Salva la Figure come immagine PNG nella cartella dei dati."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(chart_file)


def save_hours_by_platform_chart(hours_by_platform: pd.Series) -> None:
    """Salva il grafico delle ore per piattaforma."""
    save_figure(create_hours_by_platform_figure(hours_by_platform), PLATFORM_CHART_FILE)


def save_status_chart(status_counts: pd.Series) -> None:
    """Salva il grafico delle partite per stato."""
    save_figure(create_status_figure(status_counts), STATUS_CHART_FILE)


def save_completions_chart(completions: pd.Series) -> None:
    """Salva il grafico delle partite completate per anno."""
    save_figure(create_completions_figure(completions), COMPLETIONS_CHART_FILE)


def save_hours_histogram(hours_per_game: pd.Series, median_hours: float) -> None:
    """Salva l'istogramma delle ore per gioco."""
    save_figure(create_hours_histogram_figure(hours_per_game, median_hours), HOURS_HISTOGRAM_FILE)
