ALLOWED_STATUSES = ["backlog", "playing", "completed", "dropped"]


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


def ask_hours_played():
    while True:
        hours_text = input("Ore giocate: ")
        try:
            hours_played = float(hours_text)
            if hours_played >= 0:
                return hours_played
            else:
                print("Numero non accettato, le ore non possono essere negative")
        except ValueError:
            print("Inserisci un valore valido (es. 12.5)")


games = []

while True:
    print_menu()
    choice = input("Scegli voce del menu: ")
    if choice == "1":
        title = ask_non_empty_text("Inserisci il titolo del gioco: ")
        platform = ask_non_empty_text("Inserisci la piattaforma del gioco: ")
        status = ask_status()
        hours_played = ask_hours_played()
        game = {
            "title": title,
            "platform": platform,
            "status": status,
            "hours_played": hours_played,
        }
        games.append(game)
    elif choice == "2":
        for game in games:
            print(f"- {game}")
    elif choice == "3":
        print("Torna presto!")
        break
    else:
        print("Inserisci una scelta valida")