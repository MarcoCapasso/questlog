"""Punto di ingresso di Questlog: carica la libreria e gestisce il menu principale."""

from actions import add_game, export_library, import_library, open_game, search_games, show_library
from display import print_menu
from storage import load_library


def main() -> None:
    """Avvia il programma e ripete il menu finché l'utente non esce."""
    games = load_library()

    while True:
        print_menu()
        choice = input("Scegli un'opzione: ").strip()

        if choice == "1":
            add_game(games)
        elif choice == "2":
            show_library(games)
        elif choice == "3":
            open_game(games)
        elif choice == "4":
            search_games(games)
        elif choice == "5":
            export_library(games)
        elif choice == "6":
            import_library(games)
        elif choice == "7":
            print("Alla prossima!")
            break
        else:
            print("Opzione non valida.")


if __name__ == "__main__":
    main()
