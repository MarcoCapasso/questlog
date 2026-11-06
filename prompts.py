"""Richieste all'utente con validazione dell'input."""

import math
from datetime import datetime

from display import print_library
from library import ALLOWED_STATUSES, is_valid_date_order, today_iso
from models import Game


def ask_non_empty_text(prompt: str) -> str:
    """Chiede un testo finché non è vuoto e lo restituisce senza spazi ai bordi."""
    while True:
        answer = input(prompt).strip()
        if answer != "":
            return answer
        else:
            print("Il campo non può essere vuoto.")


def ask_status() -> str:
    """Mostra gli stati ammessi e chiede di sceglierne uno, normalizzato in minuscolo."""
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


def ask_hours_played(allow_zero: bool = True) -> float:
    """Chiede le ore giocate finché non sono un numero finito, non negativo e, se richiesto, maggiore di zero."""
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


def ask_game_index(games: list[Game]) -> int:
    """Chiede il numero di un gioco mostrato in elenco e restituisce il suo indice nella lista."""
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


def ask_confirmation(prompt: str) -> bool:
    """Restituisce True solo se l'utente risponde 's'."""
    answer_confirm = input(prompt).strip().lower()
    return answer_confirm == "s"


def ask_rating(prompt: str) -> float | None:
    """Chiede un voto da 1 a 10 a mezzi punti; restituisce None se l'utente preme Invio."""
    while True:
        rating_text = input(prompt).strip()
        if rating_text == "":
            return None
        try:
            rating = float(rating_text)
            if not 1 <= rating <= 10:
                print("Inserire un voto tra (1-10). Mezzi voti ammessi.")
            elif not (rating * 2).is_integer():
                print("Sono ammessi solo voti interi o mezzi punti (es. 7.5).")
            else:
                return rating
        except ValueError:
            print("Inserire un numero.")


def ask_date(prompt: str) -> str | None:
    """Chiede una data in formato GG/MM/AAAA e la restituisce in ISO; None se l'utente preme Invio."""
    while True:
        date_text = input(prompt).strip()
        if date_text == "":
            return None
        try:
            parsed_date = datetime.strptime(date_text, "%d/%m/%Y")
            iso_date = parsed_date.date().isoformat()
            if iso_date > today_iso():
                print("La data non può essere nel futuro.")
            else:
                return iso_date
        except ValueError:
            print("Data non valida. Es. 20/03/2025.")


def ask_completion_date(prompt: str, start_date: str | None) -> str | None:
    """Chiede la data di completamento finché non precede la data di inizio; None se l'utente preme Invio."""
    while True:
        completion_date = ask_date(prompt)
        if is_valid_date_order(start_date, completion_date):
            return completion_date
        print("La data di completamento non può precedere la data di inizio.")


def select_game_index(games: list[Game]) -> int | None:
    """Mostra la libreria e restituisce l'indice scelto, oppure None se la libreria è vuota."""
    print_library(games)
    if len(games) == 0:
        return None
    else:
        return ask_game_index(games)