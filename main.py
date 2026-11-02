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


while True:
    print_menu()
    choice = input("Scegli voce del menu: ")
    if choice == "1":
        title = ask_non_empty_text("Inserisci il titolo del gioco: ")
        platform = ask_non_empty_text("Inserisci la piattaforma del gioco: ")
        status = ask_status()
        print(f"Hai registrato [{title}], giocato su [{platform}], stato: [{status}].")
    elif choice == "2":
        print("Funzionalità in arrivo")
    elif choice == "3":
        print("Torna presto!")
        break
    else:
        print("Inserisci una scelta valida")