"""Richieste all'utente con validazione dell'input."""

import math

from display import print_library
from library import ALLOWED_STATUSES
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


def select_game_index(games: list[Game]) -> int | None:
    """Mostra la libreria e restituisce l'indice scelto, oppure None se la libreria è vuota."""
    print_library(games)
    if len(games) == 0:
        return None
    else:
        return ask_game_index(games)