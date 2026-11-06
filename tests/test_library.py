from library import (
    apply_status_change,
    find_game_indices_by_status,
    find_game_indices_by_title,
    is_duplicate_game,
    is_valid_date_order,
)
from models import Game


TODAY = "2026-11-06"


def make_game(
    title: str,
    platform: str = "PC",
    status: str = "backlog",
    hours_played: float = 0.0,
    rating: float | None = None,
    start_date: str | None = None,
    completion_date: str | None = None,
) -> Game:
    return Game(
        title=title,
        platform=platform,
        status=status,
        hours_played=hours_played,
        rating=rating,
        start_date=start_date,
        completion_date=completion_date,
    )


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


def test_starting_backlog_game_sets_start_date():
    game = make_game("Halo", status="backlog")
    apply_status_change(game, "playing", TODAY)
    assert game.status == "playing"
    assert game.start_date == TODAY
    assert game.completion_date is None


def test_completing_game_keeps_existing_start_date():
    game = make_game("Halo", status="playing", hours_played=10.0, start_date="2026-01-10")
    apply_status_change(game, "completed", TODAY)
    assert game.status == "completed"
    assert game.start_date == "2026-01-10"
    assert game.completion_date == TODAY


def test_reopening_completed_game_removes_completion_date():
    game = make_game(
        "Halo",
        status="completed",
        hours_played=30.0,
        start_date="2026-01-10",
        completion_date="2026-03-02",
    )
    apply_status_change(game, "playing", TODAY)
    assert game.status == "playing"
    assert game.start_date == "2026-01-10"
    assert game.completion_date is None


def test_returning_to_backlog_clears_dates_and_rating():
    game = make_game("Halo", status="playing", rating=7.5, start_date="2026-01-10")
    apply_status_change(game, "backlog", TODAY)
    assert game.status == "backlog"
    assert game.start_date is None
    assert game.rating is None


def test_completion_before_start_is_invalid():
    assert not is_valid_date_order("2026-03-10", "2026-01-05")


def test_missing_date_is_always_valid_order():
    assert is_valid_date_order(None, "2026-01-05")
    assert is_valid_date_order("2026-03-10", None)