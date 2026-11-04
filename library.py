"""Regole e ricerche sulla libreria, senza interazione con l'utente."""

ALLOWED_STATUSES = ["backlog", "playing", "completed", "dropped"]


def find_game_indices_by_title(games, query):
    matching_indices = []
    normalized_query = query.lower()

    for index, game in enumerate(games):
        if normalized_query in game['title'].lower():
            matching_indices.append(index)
    return matching_indices


def find_game_indices_by_status(games, status):
    matching_indices = []

    for index, game in enumerate(games):
        if status == game['status']:
            matching_indices.append(index)
    return matching_indices


def is_duplicate_game(games, title, platform, ignore_index=None):
    for index, game in enumerate(games):
        if index == ignore_index:
            continue
        same_title = game["title"].lower() == title.lower()
        same_platform = game["platform"].lower() == platform.lower()
        if same_title and same_platform:
            return True
    return False