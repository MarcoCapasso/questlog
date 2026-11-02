ALLOWED_STATUSES = ["backlog", "playing", "completed", "dropped"]


def print_menu():
    print()
    print("--- Questlog ---")
    print("1. Aggiungi gioco")
    print("2. Mostra libreria")
    print("3. Esci")


while True:
    print_menu()
    choice = input("Scegli voce del menu: ")
    if choice == "1":
        print("Funzionalità in arrivo")
    elif choice == "2":
        print("Funzionalità in arrivo")
    elif choice == "3":
        print("Torna presto!")
        break
    else:
        print("Inserisci una scelta valida")
