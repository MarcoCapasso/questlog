"""Azioni del menu: coordinano richieste, regole, stampa e salvataggio."""

from analysis import (
    average_rating,
    completion_rate,
    completions_per_year,
    days_to_complete,
    games_to_dataframe,
    hours_by_platform,
    hours_per_game,
    playthrough_rows,
    playthroughs_by_status,
)
from charts import (
    COMPLETIONS_CHART_FILE,
    HOURS_HISTOGRAM_FILE,
    PLATFORM_CHART_FILE,
    STATUS_CHART_FILE,
    save_completions_chart,
    save_hours_by_platform_chart,
    save_hours_histogram,
    save_status_chart,
)
from csv_io import CSV_FILE, export_csv, import_csv
from display import (
    print_game_details,
    print_game_menu,
    print_library,
    print_playthrough_edit_menu,
    print_search_menu,
    print_search_results,
    print_statistics,
)
from library import (
    PLAYTHROUGH_STATUSES,
    SEARCH_STATUSES,
    apply_status_change,
    find_game_index_by_title,
    find_game_indices_by_status,
    find_game_indices_by_title,
    find_platform_spelling,
    is_backlog,
    is_valid_date_order,
    remove_playthrough,
    today_iso,
)
from models import Game, Playthrough
from prompts import (
    ask_completion_date,
    ask_confirmation,
    ask_date,
    ask_hours_played,
    ask_non_empty_text,
    ask_rating,
    ask_status,
    select_game_index,
    select_playthrough_index,
)
from storage import save_library


def ask_new_playthrough(games: list[Game]) -> Playthrough:
    """Chiede i dati di una nuova partita, riusando la grafia delle piattaforme già in libreria."""
    platform = find_platform_spelling(games, ask_non_empty_text("Piattaforma: "))
    status = ask_status(PLAYTHROUGH_STATUSES)
    hours_played = ask_hours_played(allow_zero=status != "completed")
    start_date = ask_date("Data inizio (GG/MM/AAAA, Invio = oggi): ")
    completion_date = None
    if status == "completed":
        completion_date = ask_completion_date("Data completamento (GG/MM/AAAA, Invio = oggi): ", start_date)

    playthrough = Playthrough(platform, status, hours_played, start_date, completion_date)
    apply_status_change(playthrough, status, today_iso())
    return playthrough


def add_game(games: list[Game]) -> None:
    """Aggiunge un gioco; se il titolo esiste già propone di aggiungergli una partita."""
    title = ask_non_empty_text("Titolo: ")
    existing_index = find_game_index_by_title(games, title)

    if existing_index is not None:
        existing_game = games[existing_index]
        if ask_confirmation(f"'{existing_game.title}' è già in libreria. Aggiungere una nuova partita? (s/n): "):
            existing_game.playthroughs.append(ask_new_playthrough(games))
            save_library(games)
            print("Partita aggiunta.")
        else:
            print("Nessuna modifica.")
        return

    game = Game(title)
    if ask_confirmation("Hai già iniziato a giocarci? (s/n): "):
        game.playthroughs.append(ask_new_playthrough(games))
        game.rating = ask_rating("Voto (1-10, Invio per saltare): ")
    games.append(game)
    save_library(games)
    print(f"'{game.title}' aggiunto alla libreria.")


def show_library(games: list[Game]) -> None:
    """Mostra la libreria."""
    print_library(games)


def search_games(games: list[Game]) -> None:
    """Cerca i giochi per titolo o per stato e mostra i risultati."""
    if len(games) == 0:
        print("Libreria vuota, aggiungi prima qualche gioco.")
        return

    print_search_menu()
    choice = input("Scegli un'opzione: ").strip()
    if choice == "1":
        query = ask_non_empty_text("Testo da cercare nel titolo: ")
        print_search_results(games, find_game_indices_by_title(games, query), query)
    elif choice == "2":
        status = ask_status(SEARCH_STATUSES)
        print_search_results(games, find_game_indices_by_status(games, status), status)
    else:
        print("Opzione non valida.")


def open_game(games: list[Game]) -> None:
    """Apre la scheda di un gioco e gestisce le sue azioni finché l'utente torna alla libreria."""
    game_index = select_game_index(games)
    if game_index is None:
        return
    game = games[game_index]

    while True:
        print_game_details(game)
        print_game_menu()
        choice = input("Scegli un'opzione: ").strip()

        if choice == "1":
            add_playthrough(games, game)
        elif choice == "2":
            edit_playthrough(games, game)
        elif choice == "3":
            delete_playthrough(games, game)
        elif choice == "4":
            edit_title(games, game_index)
        elif choice == "5":
            edit_rating(games, game)
        elif choice == "6":
            if delete_game(games, game_index):
                return
        elif choice == "7":
            return
        else:
            print("Opzione non valida.")


def add_playthrough(games: list[Game], game: Game) -> None:
    """Aggiunge una partita al gioco; se era in backlog propone anche il voto."""
    was_backlog = is_backlog(game)
    game.playthroughs.append(ask_new_playthrough(games))
    if was_backlog:
        game.rating = ask_rating("Voto (1-10, Invio per saltare): ")
    save_library(games)
    print("Partita aggiunta.")


def delete_playthrough(games: list[Game], game: Game) -> None:
    """Elimina una partita dopo conferma; se era l'ultima il gioco torna in backlog."""
    playthrough_index = select_playthrough_index(game)
    if playthrough_index is None:
        return

    prompt = "Eliminare la partita? (s/n): "
    if len(game.playthroughs) == 1:
        prompt = "È l'unica partita: il gioco tornerà in backlog e perderà il voto. Eliminare? (s/n): "
    if not ask_confirmation(prompt):
        print("Eliminazione annullata.")
        return

    remove_playthrough(game, playthrough_index)
    save_library(games)
    print("Partita eliminata.")


def edit_title(games: list[Game], game_index: int) -> None:
    """Modifica il titolo, rifiutando quelli già presenti in un altro gioco."""
    new_title = ask_non_empty_text("Nuovo titolo: ")
    if find_game_index_by_title(games, new_title, ignore_index=game_index) is not None:
        print(f"Esiste già un gioco chiamato '{new_title}'.")
        return
    games[game_index].title = new_title
    save_library(games)
    print("Titolo aggiornato.")


def edit_rating(games: list[Game], game: Game) -> None:
    """Modifica il voto; Invio lo rimuove. Un gioco in backlog non si può votare."""
    if is_backlog(game):
        print("Aggiungi prima una partita: un gioco mai iniziato non si può votare.")
        return
    game.rating = ask_rating("Nuovo voto (1-10, Invio per rimuoverlo): ")
    save_library(games)
    print("Voto aggiornato.")


def delete_game(games: list[Game], game_index: int) -> bool:
    """Elimina il gioco dopo conferma e restituisce True se è stato eliminato."""
    game = games[game_index]
    if not ask_confirmation(f"Eliminare '{game.title}' e tutte le sue partite? (s/n): "):
        print("Eliminazione annullata.")
        return False
    games.pop(game_index)
    save_library(games)
    print(f"'{game.title}' eliminato.")
    return True


def edit_playthrough(games: list[Game], game: Game) -> None:
    """Sceglie una partita e ne modifica un campo."""
    playthrough_index = select_playthrough_index(game)
    if playthrough_index is None:
        return
    playthrough = game.playthroughs[playthrough_index]

    print_playthrough_edit_menu()
    choice = input("Scegli un'opzione: ").strip()
    if choice == "1":
        playthrough.platform = ask_non_empty_text("Nuova piattaforma: ")
    elif choice == "2":
        if not edit_playthrough_status(playthrough):
            return
    elif choice == "3":
        playthrough.hours_played = ask_hours_played(allow_zero=playthrough.status != "completed")
    elif choice == "4":
        if not edit_playthrough_dates(playthrough):
            return
    else:
        print("Opzione non valida.")
        return
    save_library(games)
    print("Partita aggiornata.")


def edit_playthrough_status(playthrough: Playthrough) -> bool:
    """Cambia lo stato della partita e restituisce True se è stato modificato."""
    new_status = ask_status(PLAYTHROUGH_STATUSES)
    if new_status == playthrough.status:
        print("Lo stato è già questo.")
        return False

    if playthrough.status == "completed":
        if not ask_confirmation("Riaprire la partita? La data di completamento verrà rimossa. (s/n): "):
            print("Nessuna modifica.")
            return False

    if new_status == "completed" and playthrough.hours_played == 0:
        print("Una partita completata deve avere delle ore.")
        playthrough.hours_played = ask_hours_played(allow_zero=False)

    apply_status_change(playthrough, new_status, today_iso())
    return True


def edit_playthrough_dates(playthrough: Playthrough) -> bool:
    """Modifica le date della partita (Invio lascia invariata) e restituisce True se sono valide."""
    new_start_date = ask_date("Nuova data inizio (GG/MM/AAAA, Invio = invariata): ")
    if new_start_date is None:
        new_start_date = playthrough.start_date

    new_completion_date = playthrough.completion_date
    if playthrough.status == "completed":
        answer = ask_completion_date("Nuova data completamento (GG/MM/AAAA, Invio = invariata): ", new_start_date)
        if answer is not None:
            new_completion_date = answer

    if not is_valid_date_order(new_start_date, new_completion_date):
        print("La data di completamento non può precedere la data di inizio. Nessuna modifica.")
        return False

    playthrough.start_date = new_start_date
    playthrough.completion_date = new_completion_date
    return True


def export_library(games: list[Game]) -> None:
    """Esporta la libreria in CSV, se non è vuota."""
    if len(games) == 0:
        print("Libreria vuota, aggiungi prima qualche gioco.")
        return
    export_csv(games)
    print(f"Libreria esportata in '{CSV_FILE}'.")


def import_library(games: list[Game]) -> None:
    """Sostituisce la libreria con i giochi del file CSV, dopo averlo validato e chiesto conferma."""
    try:
        imported_games = import_csv(today_iso())
    except FileNotFoundError:
        print(f"File '{CSV_FILE}' non trovato: mettilo nella cartella di Questlog.")
        return
    except UnicodeDecodeError:
        print("Il file non è in UTF-8: da Excel salvalo come 'CSV UTF-8'.")
        return
    except ValueError as error:
        print(f"Import annullato, la libreria non è cambiata. {error}")
        return

    prompt = (
        f"Trovati {len(imported_games)} giochi. "
        f"La libreria attuale ({len(games)} giochi) verrà sostituita. Continuare? (s/n): "
    )
    if not ask_confirmation(prompt):
        print("Import annullato.")
        return

    games.clear()
    games.extend(imported_games)
    save_library(games)
    print("Libreria importata.")


def show_statistics(games: list[Game]) -> None:
    """Calcola e mostra le statistiche delle partite giocate e ne salva i grafici."""
    df = games_to_dataframe(games)
    if playthrough_rows(df).empty:
        print("Nessuna partita giocata: aggiungine una per vedere le statistiche.")
        return
    platform_hours = hours_by_platform(df)
    status_counts = playthroughs_by_status(df)
    game_hours = hours_per_game(df)
    playthrough_days = days_to_complete(df)
    year_completions = completions_per_year(df)
    median_hours = float(game_hours.median())
    median_days = float(playthrough_days.median())
    completion_ratio = completion_rate(df)
    rating_average = average_rating(df)

    print_statistics(
        platform_hours,
        status_counts,
        median_hours,
        median_days,
        completion_ratio,
        rating_average,
    )

    save_hours_by_platform_chart(platform_hours)
    print(f"Grafico salvato in '{PLATFORM_CHART_FILE}'.")

    save_status_chart(status_counts)
    print(f"Grafico salvato in '{STATUS_CHART_FILE}'.")

    save_hours_histogram(game_hours, median_hours)
    print(f"Grafico salvato in '{HOURS_HISTOGRAM_FILE}'.")

    if year_completions.empty:
        print("Nessuna partita completata: grafico per anno non creato.")
    else:
        save_completions_chart(year_completions)
        print(f"Grafico salvato in '{COMPLETIONS_CHART_FILE}'.")