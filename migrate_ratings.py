"""Da eseguire una volta sola: converte i voti della libreria dalla scala 1-10 alle 5 stelle.

Prima di modificare la libreria ne salva una copia in data/game_library_backup_10.json.
"""

import shutil

from core.library import MAX_RATING, convert_rating_to_five_stars
from core.repository import JsonGameRepository
from core.storage import DATA_DIR, LIBRARY_FILE

BACKUP_FILE = DATA_DIR / "game_library_backup_10.json"


def main() -> None:
    """Converte i voti, solo se la libreria contiene ancora voti oltre le 5 stelle."""
    repository = JsonGameRepository()
    games = repository.load_games()
    rated_games = [game for game in games if game.rating is not None]
    if not any(game.rating is not None and game.rating > MAX_RATING for game in rated_games):
        print("Nessun voto oltre 5: la libreria sembra già convertita, non cambio nulla.")
        return

    shutil.copy(LIBRARY_FILE, BACKUP_FILE)
    for game in rated_games:
        if game.rating is not None:
            old_rating = game.rating
            game.rating = convert_rating_to_five_stars(old_rating)
            print(f"{game.title}: {old_rating:g}/10 → {game.rating}/{MAX_RATING}")
    repository.save_games(games)
    print(f"Fatto. La versione precedente è in {BACKUP_FILE}.")


if __name__ == "__main__":
    main()
