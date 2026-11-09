"""Stampa di menu, libreria e risultati nel terminale."""

import math
from datetime import date

import pandas as pd

from library import calculate_total_hours, has_completed_playthrough, is_backlog
from models import Game, Playthrough


def print_menu() -> None:
    """Mostra il menu principale."""
    print()
    print("--- Questlog ---")
    print("1. Aggiungi gioco")
    print("2. Mostra libreria")
    print("3. Apri gioco")
    print("4. Cerca gioco")
    print("5. Mostra statistiche")
    print("6. Esporta CSV")
    print("7. Importa CSV")
    print("8. Esci")


def print_game_menu() -> None:
    """Mostra le azioni disponibili su un gioco aperto."""
    print()
    print("--- Azioni ---")
    print("1. Aggiungi partita")
    print("2. Modifica partita")
    print("3. Elimina partita")
    print("4. Modifica titolo")
    print("5. Modifica voto")
    print("6. Elimina gioco")
    print("7. Torna alla libreria")


def print_playthrough_edit_menu() -> None:
    """Mostra i campi modificabili di una partita."""
    print()
    print("--- Modifica partita ---")
    print("1. Piattaforma")
    print("2. Stato")
    print("3. Ore")
    print("4. Date")


def print_search_menu() -> None:
    """Mostra i criteri di ricerca."""
    print()
    print("--- Filtro ---")
    print("1. Titolo")
    print("2. Stato")


def print_library(games: list[Game]) -> None:
    """Mostra la libreria numerata, oppure un avviso se è vuota."""
    if len(games) == 0:
        print("Libreria vuota, aggiungi prima qualche gioco.")
    else:
        print("--- Libreria ---")
        for position, game in enumerate(games, start=1):
            print(f"{position}. {format_game_line(game)}")


def print_search_results(games: list[Game], matching_indices: list[int], query: str) -> None:
    """Mostra i giochi trovati con il loro numero nella libreria."""
    if len(matching_indices) == 0:
        print(f"Nessuna corrispondenza per '{query}'.")
    else:
        print("--- Risultati Ricerca ---")
        for index in matching_indices:
            game = games[index]
            game_number = index + 1
            print(f"{game_number}. {format_game_line(game)}")


def print_game_details(game: Game) -> None:
    """Mostra la scheda di un gioco con l'elenco delle sue partite."""
    print()
    print(f"--- {game.title} ---")
    print(f"{'Voto:':<16}{format_rating(game.rating)}")
    print(f"{'Ore totali:':<16}{calculate_total_hours(game):g}")
    print()
    if is_backlog(game):
        print("Nessuna partita: il gioco è in backlog.")
    else:
        print_playthroughs(game)


def print_playthroughs(game: Game) -> None:
    """Mostra le partite di un gioco, numerate."""
    print("Partite")
    for position, playthrough in enumerate(game.playthroughs, start=1):
        print(f"{position}. {format_playthrough_line(playthrough)}")


def print_statistics(
    hours_by_platform: pd.Series,
    status_counts: pd.Series,
    median_hours: float,
    median_days: float,
    completion_rate: float,
    average_rating: float,
) -> None:
    """Mostra le statistiche della libreria."""
    print()
    print("--- Statistiche ---")
    print(f"{'Mediana ore per gioco:':<28}{format_number(median_hours)}")
    print(f"{'Mediana giorni per finire:':<28}{format_number(median_days)}")
    print(f"{'Tasso di completamento:':<28}{format_percentage(completion_rate)}")
    print(f"{'Voto medio:':<28}{format_number(average_rating)}")
    print()
    print("Ore per piattaforma")
    for platform, hours in hours_by_platform.items():
        print(f"  {platform:<22}{hours:g}")
    print()
    print("Partite per stato")
    for status, count in status_counts.items():
        print(f"  {status:<22}{count}")


def format_game_line(game: Game) -> str:
    """Restituisce la descrizione di un gioco su una riga; un segno di spunta indica che è stato completato."""
    if is_backlog(game):
        return f"{game.title} | backlog"
    title = game.title
    if has_completed_playthrough(game):
        title = f"{title} ✓"
    return (
        f"{title} | {format_playthrough_count(game)} | "
        f"{calculate_total_hours(game):g} ore | voto: {format_rating(game.rating)}"
    )


def format_playthrough_count(game: Game) -> str:
    """Restituisce il numero di partite al singolare o al plurale."""
    count = len(game.playthroughs)
    if count == 1:
        return "1 partita"
    return f"{count} partite"


def format_playthrough_line(playthrough: Playthrough) -> str:
    """Restituisce la descrizione di una partita su una riga."""
    return (
        f"{playthrough.platform} | {playthrough.status} | {playthrough.hours_played:g} ore | "
        f"{format_date(playthrough.start_date)} → {format_date(playthrough.completion_date)}"
    )


def format_rating(rating: float | None) -> str:
    """Restituisce il voto formattato, oppure un trattino se manca."""
    if rating is None:
        return "-"
    return f"{rating:g}"


def format_date(iso_date: str | None) -> str:
    """Restituisce una data ISO nel formato GG/MM/AAAA, oppure un trattino se manca."""
    if iso_date is None:
        return "-"
    return date.fromisoformat(iso_date).strftime("%d/%m/%Y")


def format_number(value: float) -> str:
    """Restituisce il numero senza decimali superflui, oppure un trattino se non è calcolabile."""
    if math.isnan(value):
        return "-"
    return f"{value:g}"


def format_percentage(value: float) -> str:
    """Restituisce il valore come percentuale intera, oppure un trattino se non è calcolabile."""
    if math.isnan(value):
        return "-"
    return f"{value:.0%}"