"""Operazioni del menu: aggiunta, modifica, eliminazione e ricerca."""

from display import (
    format_game_line,
    format_rating,
    print_edit_menu,
    print_search_menu,
    print_search_results,
)
from library import (
    apply_status_change,
    find_game_indices_by_status,
    find_game_indices_by_title,
    is_duplicate_game,
    today_iso,
)
from models import Game
from prompts import (
    ask_confirmation,
    ask_hours_played,
    ask_non_empty_text,
    ask_rating,
    ask_status,
    select_game_index,
)


def add_game(games: list[Game]) -> None:
    """Chiede i dati di un nuovo gioco e lo aggiunge alla libreria, se non è un duplicato."""
    title = ask_non_empty_text("Inserisci il titolo del gioco: ")
    platform = ask_non_empty_text("Inserisci la piattaforma del gioco: ")
    if is_duplicate_game(games, title, platform):
        print(f"'{title}' su {platform} è già presente in libreria.")
    else:
        status = ask_status()
        if status == "backlog":
            hours_played = 0.0
            rating = None
        elif status == "completed":
            hours_played = ask_hours_played(allow_zero=False)
            rating = ask_rating("Voto (1-10, Invio per saltare): ")
        else:
            hours_played = ask_hours_played()
            rating = ask_rating("Voto (1-10, Invio per saltare): ")
        game = Game(
            title=title,
            platform=platform,
            status=status,
            hours_played=hours_played,
            rating=rating,
        )
        games.append(game)
        print(f"'{title}' aggiunto alla libreria.")


def delete_game(games: list[Game]) -> None:
    """Fa scegliere un gioco e lo elimina dopo conferma."""
    game_index = select_game_index(games)
    if game_index is not None:
        selected_game = games[game_index]
        confirm_delete = ask_confirmation(f"Sei sicuro di voler eliminare '{format_game_line(selected_game)}'? (s/n) ")
        if confirm_delete:
            games.pop(game_index)
            print(f"'{selected_game.title}' eliminato dalla libreria.")
        else:
            print("Nessun gioco eliminato.")


def edit_game(games: list[Game]) -> None:
    """Fa scegliere un gioco e il campo da modificare."""
    game_index = select_game_index(games)
    if game_index is not None:
        selected_game = games[game_index]
        print(f"Hai selezionato '{selected_game.title}'.")
        print_edit_menu()
        field_choice = ask_non_empty_text("Quale campo vuoi modificare? ")
        if field_choice == "1":
            edit_game_title(games, game_index)
        elif field_choice == "2":
            edit_game_platform(games, game_index)
        elif field_choice == "3":
            edit_game_status(selected_game)
        elif field_choice == "4":
            edit_game_hours(selected_game)
        elif field_choice == "5":
            edit_game_rating(selected_game)
        else:
            print("Inserisci una scelta valida.")


def edit_game_title(games: list[Game], game_index: int) -> None:
    """Modifica il titolo di un gioco, rifiutando i duplicati."""
    selected_game = games[game_index]
    new_title = ask_non_empty_text("Inserisci il nuovo titolo: ")
    if is_duplicate_game(games, new_title, selected_game.platform, ignore_index=game_index):
        print(f"'{new_title}' su {selected_game.platform} è già presente in libreria.")
    else:
        selected_game.title = new_title
        print(f"Titolo aggiornato in '{new_title}'.")


def edit_game_platform(games: list[Game], game_index: int) -> None:
    """Modifica la piattaforma di un gioco, rifiutando i duplicati."""
    selected_game = games[game_index]
    new_platform = ask_non_empty_text("Inserisci la nuova piattaforma: ")
    if is_duplicate_game(games, selected_game.title, new_platform, ignore_index=game_index):
        print(f"'{selected_game.title}' su {new_platform} è già presente in libreria.")
    else:
        selected_game.platform = new_platform
        print(f"Piattaforma aggiornata in '{new_platform}'.")


def edit_game_status(game: Game) -> None:
    """Modifica lo stato di un gioco rispettando le regole su ore, date e voto."""
    new_status = ask_status()
    if new_status == "backlog":
        if game.hours_played > 0:
            print("Un gioco iniziato non può tornare in backlog.")
            return
        if game.start_date is not None or game.rating is not None:
            if not ask_confirmation("Il gioco tornerà in backlog: voto e data di inizio verranno rimossi. Confermi? (s/n) "):
                print("Nessuna modifica effettuata.")
                return
        apply_status_change(game, new_status, today_iso())
        print(f"Stato aggiornato in '{new_status}'.")
    elif new_status == "completed":
        if game.hours_played > 0:
            current_hours = game.hours_played
            if ask_confirmation(f"Vuoi aggiornare le ore? Attuali: {current_hours:g} (s/n) "):
                game.hours_played = ask_hours_played(allow_zero=False)
        else:
            game.hours_played = ask_hours_played(allow_zero=False)
        apply_status_change(game, new_status, today_iso())
        print(f"Stato aggiornato in '{new_status}', ore: {game.hours_played:g}.")
    else:
        if game.status == "completed" and game.completion_date is not None:
            if not ask_confirmation("Il gioco non sarà più completato e la data di completamento verrà rimossa. Confermi? (s/n) "):
                print("Nessuna modifica effettuata.")
                return
        apply_status_change(game, new_status, today_iso())
        print(f"Stato aggiornato in '{new_status}'.")


def edit_game_hours(game: Game) -> None:
    """Modifica le ore di un gioco; un gioco in backlog passa a playing dopo conferma."""
    if game.status == "backlog":
        if ask_confirmation("Il gioco passerà da 'backlog' a 'playing'. Confermi? (s/n) "):
            game.hours_played = ask_hours_played(allow_zero=False)
            apply_status_change(game, "playing", today_iso())
            print(f"Stato aggiornato in 'playing', ore: {game.hours_played:g}.")
        else:
            print("Nessuna modifica effettuata.")
    elif game.status == "completed":
        game.hours_played = ask_hours_played(allow_zero=False)
        print(f"Ore aggiornate: {game.hours_played:g}.")
    else:
        game.hours_played = ask_hours_played()
        print(f"Ore aggiornate: {game.hours_played:g}.")


def edit_game_rating(game: Game) -> None:
    """Modifica il voto di un gioco; un gioco in backlog non può avere un voto."""
    if game.status == "backlog":
        print("Un gioco in backlog non può avere un voto: cambia prima lo stato")
    else:
        new_rating = ask_rating(f"Nuovo voto (attuale: {format_rating(game.rating)}, Invio per lasciarlo): ")
        if new_rating is None:
            print("Nessuna modifica effettuata")
        else:
            game.rating = new_rating
            print(f"Voto aggiornato: {format_rating(game.rating)}")


def search_games(games: list[Game]) -> None:
    """Fa scegliere il criterio di ricerca e mostra i giochi trovati."""
    print_search_menu()
    search_choice = ask_non_empty_text("Filtra per: ")
    if search_choice == "1":
        search_text = ask_non_empty_text("Cerca un titolo: ")
        matching_indices = find_game_indices_by_title(games, search_text)
        print_search_results(games, matching_indices, search_text)
    elif search_choice == "2":
        selected_status = ask_status()
        matching_indices = find_game_indices_by_status(games, selected_status)
        print_search_results(games, matching_indices, selected_status)
    else:
        print("Inserisci una scelta valida.")