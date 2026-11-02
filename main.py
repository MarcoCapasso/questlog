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


while True:
    print_menu()
    choice = input("Scegli voce del menu: ")
    if choice == "1":
        status = ask_status()
        print(f"Stato inserito: {status}")
    elif choice == "2":
        print("Funzionalità in arrivo")
    elif choice == "3":
        print("Torna presto!")
        break
    else:
        print("Inserisci una scelta valida")