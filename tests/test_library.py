from library import (
    find_game_indices_by_status,
    find_game_indices_by_title,
    is_duplicate_game,
)
from models import Game


def make_game(
    title: str,
    platform: str = "PC",
    status: str = "backlog",
    hours_played: float = 0.0,
) -> Game:
    return Game(title, platform, status, hours_played)


def test_find_by_title_is_case_insensitive():
    games = [
        make_game("The Legend of Zelda"),
        make_game("Doom"),
    ]
    result = find_game_indices_by_title(games, "ZELDA")
    assert result == [0]


def test_find_by_title_matches_partial_text():
    games = [
        make_game("The Legend of Zelda"),
        make_game("Doom"),
    ]
    result = find_game_indices_by_title(games, "Zel")
    assert result == [0]


def test_find_by_title_returns_all_matches():
    games = [
        make_game("The Legend of Zelda"),
        make_game("Doom"),
        make_game("The Legend of Zelda II"),
    ]
    result = find_game_indices_by_title(games, "Zelda")
    assert result == [0, 2]


def test_find_by_title_returns_empty_list_when_no_match():
    games = [
        make_game("The Legend of Zelda"),
        make_game("Doom"),
        make_game("The Legend of Zelda II"),
    ]
    result = find_game_indices_by_title(games, "Halo")
    assert result == []


def test_find_by_status_returns_only_matching_status():
    games = [
        make_game("The Legend of Zelda", status="backlog"),
        make_game("Doom", status="completed"),
        make_game("The Legend of Zelda II", status="dropped"),
        make_game("Outer Wilds", status="backlog"),
    ]
    result = find_game_indices_by_status(games, "backlog")
    assert result == [0, 3]


def test_duplicate_detected_ignoring_case():
    games = [
        make_game("Outer Wilds", platform="Nintendo Switch 2"),
        make_game("Halo", platform="Xbox"),
        make_game("Halo", platform="PC"),
        make_game("Doom", platform="Xbox"),
    ]
    result = is_duplicate_game(games, "HALO", "xbox")
    assert result


def test_same_title_on_other_platform_is_not_duplicate():
    games = [
        make_game("Halo", platform="Xbox"),
        make_game("Halo", platform="PC"),
    ]
    result = is_duplicate_game(games, "Halo", "PS5")
    assert not result


def test_duplicate_ignores_game_being_edited():
    games = [
        make_game("Halo", platform="PC"),
        make_game("Doom", platform="PC"),
    ]
    assert not is_duplicate_game(games, "halo", "PC", ignore_index=0)
    assert is_duplicate_game(games, "doom", "PC", ignore_index=0)