ALLOWED_STATUSES = ["backlog", "playing", "completed", "dropped"]


games = []


def print_menu():
    print()
    print("--- Questlog ---")
    print("1. Aggiungi gioco")
    print("2. Mostra libreria")
    print("3. Esci")


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


def ask_non_empty_text(prompt):
    while True:
        answer = input(prompt).strip()
        if answer != "":
            return answer
        else:
            print("Il campo non può essere vuoto.")


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


def print_library(games):
    if len(games) == 0:
        print("Libreria vuota, aggiungi prima qualche gioco.")
    else:
        print("--- Libreria ---")
        for game in games:
            print_game_line(game)


def print_game_line(game):
    if game["status"] == "backlog":
        print(f"- {game['title']} ({game['platform']}) | {game['status']}")
    else:
        print(f"- {game['title']} ({game['platform']}) | {game['status']} | {game['hours_played']:g} ore")


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
        print("Torna presto!")
        break
    else:
        print("Inserisci una scelta valida")