ALLOWED_STATUSES = ["backlog", "playing", "completed", "dropped"]


games = []


def print_menu():
    print()
    print("--- Questlog ---")
    print("1. Aggiungi gioco")
    print("2. Mostra libreria")
    print("3. Elimina gioco")
    print("4. Esci")


def ask_non_empty_text(prompt):
    while True:
        answer = input(prompt).strip()
        if answer != "":
            return answer
        else:
            print("Il campo non può essere vuoto.")


def ask_status():
    print()
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
            if hours_played < 0:
                print("Le ore non possono essere inferiori a 0.")
            elif hours_played == 0 and not allow_zero:
                print("Le ore devono essere maggiori di 0")
            else:
                return hours_played
        except ValueError:
            print("Inserisci un valore valido. (es. 12.5)")


def ask_game_index(games):
    while True:
        number_text = input(f"Inserisci numero del gioco tra 1 e {len(games)}: ")
        try:
            game_number = int(number_text)
            if 1 <= game_number <= len(games):
                index = game_number - 1
                return index
            else:
                print(f"Numero non valido, inserisci un numero compreso tra 1 e {len(games)}")
        except ValueError:
            print("Inserisci un numero")


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


def is_duplicate_game(games, title, platform):
    for game in games:
        same_title = game["title"].lower() == title.lower()
        same_platform = game["platform"].lower() == platform.lower()
        if same_title and same_platform:
            return True
    return False


while True:
    print_menu()
    choice = input("Scegli voce del menu: ")
    if choice == "1":
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
                hours_played = ask_hours_played(allow_zero=True)
            game = {
                "title": title,
                "platform": platform,
                "status": status,
                "hours_played": hours_played,
            }
            games.append(game)
            print(f"'{title}' aggiunto alla libreria. ")

    elif choice == "2":
        print_library(games)

    elif choice == "3":
        print_library(games)
        if len(games) != 0:
            game_index = ask_game_index(games)
            selected_game = games[game_index]
            confirm_delete = ask_confirmation(f"Sei sicuro di voler eliminare '{format_game_line(selected_game)}'? (s/n) ")
            if confirm_delete:
                games.pop(game_index)
                print(f"'{selected_game['title']}' eliminato dalla libreria")
            else:
                print("Nessun gioco eliminato.")

    elif choice == "4":
        print("Torna presto!")
        break

    else:
        print("Inserisci una scelta valida")