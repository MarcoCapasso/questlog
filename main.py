import json
import math


ALLOWED_STATUSES = ["backlog", "playing", "completed", "dropped"]
LIBRARY_FILE = "game_library.json"


def save_library(games):
    with open(LIBRARY_FILE, "w", encoding="utf-8") as file:
        json.dump(games, file, indent=4, ensure_ascii=False)


def load_library():
    with open(LIBRARY_FILE, "r", encoding="utf-8") as file:
        games = json.load(file)
        return games


def print_menu():
    print()
    print("--- Questlog ---")
    print("1. Aggiungi gioco")
    print("2. Mostra libreria")
    print("3. Cerca gioco")
    print("4. Modifica gioco")
    print("5. Elimina gioco")
    print("6. Esci")


def print_edit_menu():
    print()
    print("--- Modifica ---")
    print("1. Titolo")
    print("2. Piattaforma")
    print("3. Stato")
    print("4. Ore")


def print_search_menu():
    print()
    print("--- Filtro ---")
    print("1. Titolo")
    print("2. Stato")


def add_game(games):
    title = ask_non_empty_text("Inserisci il titolo del gioco: ")
    platform = ask_non_empty_text("Inserisci la piattaforma del gioco: ")
    if is_duplicate_game(games, title, platform):
        print(f"'{title}' su {platform} è già presente in libreria.")
    else:
        status = ask_status()
        if status == "backlog":
            hours_played = 0.0
        elif status == "completed":
            hours_played = ask_hours_played(allow_zero=False)
        else:
            hours_played = ask_hours_played()
        game = {
            "title": title,
            "platform": platform,
            "status": status,
            "hours_played": hours_played,
        }
        games.append(game)
        print(f"'{title}' aggiunto alla libreria.")


def delete_game(games):
    game_index = select_game_index(games)
    if game_index is not None:
        selected_game = games[game_index]
        confirm_delete = ask_confirmation(f"Sei sicuro di voler eliminare '{format_game_line(selected_game)}'? (s/n) ")
        if confirm_delete:
            games.pop(game_index)
            print(f"'{selected_game['title']}' eliminato dalla libreria.")
        else:
            print("Nessun gioco eliminato.")


def edit_game(games):
    game_index = select_game_index(games)
    if game_index is not None:
        selected_game = games[game_index]
        print(f"Hai selezionato '{selected_game['title']}'.")
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
        else:
            print("Inserisci una scelta valida.")


def edit_game_title(games, game_index):
    selected_game = games[game_index]
    new_title = ask_non_empty_text("Inserisci il nuovo titolo: ")
    if is_duplicate_game(games, new_title, selected_game["platform"], ignore_index=game_index):
        print(f"'{new_title}' su {selected_game['platform']} è già presente in libreria.")
    else:
        selected_game["title"] = new_title
        print(f"Titolo aggiornato in '{new_title}'.")


def edit_game_platform(games, game_index):
    selected_game = games[game_index]
    new_platform = ask_non_empty_text("Inserisci la nuova piattaforma: ")
    if is_duplicate_game(games, selected_game["title"], new_platform, ignore_index=game_index):
        print(f"'{selected_game['title']}' su {new_platform} è già presente in libreria.")
    else:
        selected_game["platform"] = new_platform
        print(f"Piattaforma aggiornata in '{new_platform}'.")


def edit_game_status(game):
    new_status = ask_status()
    if new_status == "backlog":
        if game["hours_played"] > 0:
            print("Un gioco iniziato non può tornare in backlog.")
        else:
            game["status"] = new_status
            print(f"Stato aggiornato in '{new_status}'.")
    elif new_status == "completed":
        if game["hours_played"] > 0:
            current_hours = game["hours_played"]
            if ask_confirmation(f"Vuoi aggiornare le ore? Attuali: {current_hours:g} (s/n) "):
                game["hours_played"] = ask_hours_played(allow_zero=False)
        else:
            game["hours_played"] = ask_hours_played(allow_zero=False)
        game["status"] = new_status
        print(f"Stato aggiornato in '{new_status}', ore: {game['hours_played']:g}.")
    else:
        game["status"] = new_status
        print(f"Stato aggiornato in '{new_status}'.")


def edit_game_hours(game):
    if game["status"] == "backlog":
        if ask_confirmation("Il gioco passerà da 'backlog' a 'playing'. Confermi? (s/n) "):
            game["hours_played"] = ask_hours_played(allow_zero=False)
            game["status"] = "playing"
            print(f"Stato aggiornato in 'playing', ore: {game['hours_played']:g}.")
        else:
            print("Nessuna modifica effettuata.")
    elif game["status"] == "completed":
        game["hours_played"] = ask_hours_played(allow_zero=False)
        print(f"Ore aggiornate: {game['hours_played']:g}.")
    else:
        game["hours_played"] = ask_hours_played()
        print(f"Ore aggiornate: {game['hours_played']:g}.")


def find_game_indices_by_title(games, query):
    matching_indices = []
    normalized_query = query.lower()

    for index, game in enumerate(games):
        if normalized_query in game['title'].lower():
            matching_indices.append(index)
    return matching_indices


def find_game_indices_by_status(games, status):
    matching_indices = []

    for index, game in enumerate(games):
        if status == game['status']:
            matching_indices.append(index)
    return matching_indices


def print_search_results(games, matching_indices, query):
    if len(matching_indices) == 0:
        print(f"Nessuna corrispondenza per '{query}'.")
    else:
        print("--- Risultati Ricerca ---")
        for index in matching_indices:
            game = games[index]
            game_number = index + 1
            print(f"{game_number}. {format_game_line(game)}")


def search_games(games):
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
        print("Inserisci un filtro valido.")


def ask_non_empty_text(prompt):
    while True:
        answer = input(prompt).strip()
        if answer != "":
            return answer
        else:
            print("Il campo non può essere vuoto.")


def ask_status():
    print()
    print("--- Seleziona uno stato ---")
    for status in ALLOWED_STATUSES:
        print(f"- {status}")
    while True:
        game_status = input("Inserisci stato del gioco: ").strip().lower()
        if game_status in ALLOWED_STATUSES:
            return game_status
        else:
            print("Inserisci uno stato valido.")


def ask_hours_played(allow_zero=True):
    while True:
        hours_text = input("Ore giocate: ")
        try:
            hours_played = float(hours_text)
            if not math.isfinite(hours_played):
                print("Inserisci un valore valido (es. 12.5).")
            elif hours_played < 0:
                print("Le ore non possono essere inferiori a 0.")
            elif hours_played == 0 and not allow_zero:
                print("Le ore devono essere maggiori di 0.")
            else:
                return hours_played
        except ValueError:
            print("Inserisci un valore valido (es. 12.5).")


def ask_game_index(games):
    while True:
        number_text = input(f"Inserisci numero del gioco tra 1 e {len(games)}: ")
        try:
            game_number = int(number_text)
            if 1 <= game_number <= len(games):
                index = game_number - 1
                return index
            else:
                print(f"Numero non valido, inserisci un numero compreso tra 1 e {len(games)}.")
        except ValueError:
            print("Inserisci un numero.")


def select_game_index(games):
    print_library(games)
    if len(games) == 0:
        return None
    else:
        return ask_game_index(games)


def ask_confirmation(prompt):
    answer_confirm = input(prompt).strip().lower()
    return answer_confirm == "s"


def print_library(games):
    if len(games) == 0:
        print("Libreria vuota, aggiungi prima qualche gioco.")
    else:
        print("--- Libreria ---")
        for position, game in enumerate(games, start=1):
            print(f"{position}. {format_game_line(game)}")


def format_game_line(game):
    if game["status"] == "backlog":
        return f"{game['title']} ({game['platform']}) | {game['status']}"
    else:
        return f"{game['title']} ({game['platform']}) | {game['status']} | {game['hours_played']:g} ore"


def is_duplicate_game(games, title, platform, ignore_index=None):
    for index, game in enumerate(games):
        if index == ignore_index:
            continue
        same_title = game["title"].lower() == title.lower()
        same_platform = game["platform"].lower() == platform.lower()
        if same_title and same_platform:
            return True
    return False


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