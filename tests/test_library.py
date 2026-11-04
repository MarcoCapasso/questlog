from library import (
    find_game_indices_by_title,
    find_game_indices_by_status,
    is_duplicate_game,
)


def test_find_by_title_is_case_insensitive():
    games = [
        {"title": "The Legend of Zelda"},
        {"title": "Doom"},
    ]
    result = find_game_indices_by_title(games, "ZELDA")
    assert result == [0]


def test_find_by_title_matches_partial_text():
    games = [
        {"title": "The Legend of Zelda"},
        {"title": "Doom"},
    ]
    result = find_game_indices_by_title(games, "Zel")
    assert result == [0]


def test_find_by_title_returns_all_matches():
    games = [
        {"title": "The Legend of Zelda"},
        {"title": "Doom"},
        {"title": "The Legend of Zelda II"},
    ]
    result = find_game_indices_by_title(games, "Zelda")
    assert result == [0, 2]


def test_find_by_title_returns_empty_list_when_no_match():
    games = [
        {"title": "The Legend of Zelda"},
        {"title": "Doom"},
        {"title": "The Legend of Zelda II"},
    ]
    result = find_game_indices_by_title(games, "Halo")
    assert result == []


def test_find_by_status_returns_only_matching_status():
    games = [
        {"title": "The Legend of Zelda", "status": "backlog"},
        {"title": "Doom", "status": "completed"},
        {"title": "The Legend of Zelda II", "status": "dropped"},
        {"title": "Outer Wilds", "status": "backlog"},
    ]
    result = find_game_indices_by_status(games, "backlog")
    assert result == [0, 3]


def test_duplicate_detected_ignoring_case():
    games = [
        {"title": "Outer Wilds", "platform": "Nintendo Switch 2"},
        {"title": "Halo", "platform": "Xbox"},
        {"title": "Halo", "platform": "Pc"},
        {"title": "Doom", "platform": "Xbox"},
    ]
    result = is_duplicate_game(games, "HALO", "Xbox")
    assert result


def test_same_title_on_other_platform_is_not_duplicate():
    games = [
        {"title": "Halo", "platform": "PC"},
        {"title": "Doom", "platform": "PC"},
    ]
    result = is_duplicate_game(games, "Halo", "Ps5")
    assert not result


def test_duplicate_ignores_game_being_edited():
    games = [
        {"title": "Halo", "platform": "PC"},
        {"title": "Doom", "platform": "PC"},
    ]
    assert not is_duplicate_game(games, "halo", "PC", ignore_index=0)
    assert is_duplicate_game(games, "doom", "PC", ignore_index=0)