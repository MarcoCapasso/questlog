"""Stampa di menu, libreria e risultati nel terminale."""

from models import Game


def print_menu() -> None:
    """Mostra il menu principale."""
    print()
    print("--- Questlog ---")
    print("1. Aggiungi gioco")
    print("2. Mostra libreria")
    print("3. Cerca gioco")
    print("4. Modifica gioco")
    print("5. Elimina gioco")
    print("6. Esci")


def print_edit_menu() -> None:
    """Mostra i campi modificabili di un gioco."""
    print()
    print("--- Modifica ---")
    print("1. Titolo")
    print("2. Piattaforma")
    print("3. Stato")
    print("4. Ore")


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


def format_game_line(game: Game) -> str:
    """Restituisce la descrizione di un gioco su una riga; le ore non compaiono per il backlog."""
    if game.status == "backlog":
        return f"{game.title} ({game.platform}) | {game.status}"
    else:
        return f"{game.title} ({game.platform}) | {game.status} | {game.hours_played:g} ore"