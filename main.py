"""Avvio di Questlog e ciclo del menu principale."""

from actions import (
    add_game,
    delete_game,
    edit_game,
    search_games,
)
from display import print_library, print_menu
from storage import load_library, save_library


def main() -> None:
    """Carica la libreria e gestisce il menu finché l'utente non esce."""
    games = load_library()
    while True:
        print_menu()
        print()
        choice = input("Scegli voce del menu: ")
        if choice == "1":
            add_game(games)
            save_library(games)

        elif choice == "2":
            print_library(games)

        elif choice == "3":
            search_games(games)

        elif choice == "4":
            edit_game(games)
            save_library(games)

        elif choice == "5":
            delete_game(games)
            save_library(games)

        elif choice == "6":
            print("Torna presto!")
            break

        else:
            print("Inserisci una scelta valida.")


if __name__ == "__main__":
    main()