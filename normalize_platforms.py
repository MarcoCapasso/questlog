"""Da eseguire una volta: uniforma i nomi delle piattaforme già salvati ("Ps4" → "PlayStation 4").

Prima di modificare la libreria ne salva una copia in data/game_library_backup_platforms.json.
Si può rilanciare senza problemi: se i nomi sono già uniformi non cambia nulla.
"""

import shutil

from core.platforms import normalize_library_platforms
from core.repository import JsonGameRepository
from core.storage import DATA_DIR, LIBRARY_FILE

BACKUP_FILE = DATA_DIR / "game_library_backup_platforms.json"


def main() -> None:
    """Normalizza le piattaforme di tutte le partite e salva, solo se qualcosa è cambiato."""
    repository = JsonGameRepository()
    games = repository.load_games()
    before = sorted({playthrough.platform for game in games for playthrough in game.playthroughs})
    changed = normalize_library_platforms(games)
    if changed == 0:
        print("Le piattaforme sono già uniformi, non cambio nulla.")
        return

    shutil.copy(LIBRARY_FILE, BACKUP_FILE)
    repository.save_games(games)
    after = sorted({playthrough.platform for game in games for playthrough in game.playthroughs})
    print(f"Partite aggiornate: {changed}")
    print(f"Prima: {', '.join(before)}")
    print(f"Dopo:  {', '.join(after)}")
    print(f"La versione precedente è in {BACKUP_FILE}.")


if __name__ == "__main__":
    main()
