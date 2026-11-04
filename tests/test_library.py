from library import find_game_indices_by_title


def test_find_by_title_is_case_insensitive():
    games = [
        {"title": "The Legend of Zelda"},
        {"title": "Doom"},
    ]
    result = find_game_indices_by_title(games, "ZELDA")
    assert result == [0]
