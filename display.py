"""Stampa di menu, libreria e risultati nel terminale."""

from datetime import date

from models import Game


def print_menu() -> None:
    """Mostra il menu principale."""
    print()
    print("--- Questlog ---")
    print("1. Aggiungi gioco")
    print("2. Mostra libreria")
    print("3. Dettagli gioco")
    print("4. Cerca gioco")
    print("5. Modifica gioco")
    print("6. Elimina gioco")
    print("7. Esci")


def print_edit_menu() -> None:
    """Mostra i campi modificabili di un gioco."""
    print()
    print("--- Modifica ---")
    print("1. Titolo")
    print("2. Piattaforma")
    print("3. Stato")
    print("4. Ore")
    print("5. Voto")
    print("6. Date")


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
    """Mostra tutti i campi di un gioco, con un trattino per quelli mancanti."""
    print()
    print(f"--- {game.title} ---")
    print(f"{'Piattaforma:':<16}{game.platform}")
    print(f"{'Stato:':<16}{game.status}")
    print(f"{'Ore giocate:':<16}{game.hours_played:g}")
    print(f"{'Voto:':<16}{format_rating(game.rating)}")
    print(f"{'Inizio:':<16}{format_date(game.start_date)}")
    print(f"{'Completamento:':<16}{format_date(game.completion_date)}")


def format_game_line(game: Game) -> str:
    """Restituisce la descrizione di un gioco su una riga; le ore e il voto non compaiono per il backlog."""
    if game.status == "backlog":
        return f"{game.title} ({game.platform}) | {game.status}"
    return f"{game.title} ({game.platform}) | {game.status} | {game.hours_played:g} ore | voto: {format_rating(game.rating)}"


def format_rating(rating: float | None) -> str:
    """Restituisce il voto formattato, oppure un trattino se manca."""
    if rating is None:
        return "-"
    else:
        return f"{rating:g}"


def format_date(iso_date: str | None) -> str:
    """Restituisce una data ISO nel formato GG/MM/AAAA, oppure un trattino se manca."""
    if iso_date is None:
        return "-"
    return date.fromisoformat(iso_date).strftime("%d/%m/%Y")