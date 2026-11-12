from core.library import (
    BACKLOG,
    apply_status_change,
    calculate_total_hours,
    count_by_summary_status,
    current_playthrough,
    filter_games,
    find_game_index_by_title,
    find_game_indices_by_status,
    find_game_indices_by_title,
    find_platform_spelling,
    has_completed_playthrough,
    is_backlog,
    is_valid_date_order,
    is_valid_rating,
    known_platforms,
    last_activity_date,
    playthrough_statuses,
    recently_played,
    remove_playthrough,
    replace_playthrough,
    summary_status,
    validate_new_playthrough,
)
from core.models import Game, Playthrough


TODAY = "2026-03-20"


def make_playthrough(status: str = "playing", hours_played: float = 10) -> Playthrough:
    return Playthrough("PC", status, hours_played)


def make_game(title: str, *playthroughs: Playthrough) -> Game:
    return Game(title, playthroughs=list(playthroughs))


def test_search_by_title_ignores_case():
    games = [make_game("Hades"), make_game("Celeste")]

    assert find_game_indices_by_title(games, "HAD") == [0]


def test_search_by_title_returns_empty_list_when_nothing_matches():
    games = [make_game("Hades")]

    assert find_game_indices_by_title(games, "zelda") == []


def test_search_by_status_matches_any_playthrough():
    games = [
        make_game("Hades", make_playthrough("dropped"), make_playthrough("completed")),
        make_game("Celeste", make_playthrough("playing")),
    ]

    assert find_game_indices_by_status(games, "completed") == [0]


def test_search_by_backlog_returns_games_without_playthroughs():
    games = [make_game("Hades", make_playthrough()), make_game("Celeste")]

    assert find_game_indices_by_status(games, BACKLOG) == [1]


def test_find_by_title_ignores_case():
    games = [make_game("Hades"), make_game("Celeste")]

    assert find_game_index_by_title(games, "celeste") == 1


def test_find_by_title_returns_none_when_missing():
    games = [make_game("Hades")]

    assert find_game_index_by_title(games, "Celeste") is None


def test_find_by_title_skips_ignored_index():
    games = [make_game("Hades"), make_game("Celeste")]

    assert find_game_index_by_title(games, "Hades", ignore_index=0) is None
    assert find_game_index_by_title(games, "Hades", ignore_index=1) == 0


def test_game_without_playthroughs_is_backlog():
    assert is_backlog(make_game("Hades"))
    assert not is_backlog(make_game("Hades", make_playthrough()))


def test_total_hours_sums_all_playthroughs():
    game = make_game("Hades", make_playthrough(hours_played=10), make_playthrough(hours_played=2.5))

    assert calculate_total_hours(game) == 12.5


def test_total_hours_is_zero_for_backlog_game():
    assert calculate_total_hours(make_game("Hades")) == 0


def test_has_completed_playthrough():
    assert has_completed_playthrough(make_game("Hades", make_playthrough("dropped"), make_playthrough("completed")))
    assert not has_completed_playthrough(make_game("Hades", make_playthrough("dropped")))


def test_replace_playthrough_keeps_position():
    first = Playthrough("PS4", "completed", 100)
    second = Playthrough("PS5", "playing", 5)
    game = Game("GTA V", playthroughs=[first, second])

    replace_playthrough(game, 0, Playthrough("PS4", "completed", 120))

    assert game.playthroughs == [Playthrough("PS4", "completed", 120), second]


def test_remove_playthrough_keeps_rating_when_others_remain():
    game = make_game("Hades", make_playthrough(), make_playthrough())
    game.rating = 4

    remove_playthrough(game, 0)

    assert len(game.playthroughs) == 1
    assert game.rating == 4


def test_remove_last_playthrough_clears_rating():
    game = make_game("Hades", make_playthrough())
    game.rating = 4

    remove_playthrough(game, 0)

    assert is_backlog(game)
    assert game.rating is None


def test_status_change_to_playing_sets_start_date_and_clears_completion():
    playthrough = Playthrough("PC", "completed", 10, "2026-01-01", "2026-02-01")

    apply_status_change(playthrough, "playing", TODAY)

    assert playthrough.status == "playing"
    assert playthrough.start_date == "2026-01-01"
    assert playthrough.completion_date is None


def test_status_change_to_completed_fills_missing_dates_with_today():
    playthrough = make_playthrough("playing")

    apply_status_change(playthrough, "completed", TODAY)

    assert playthrough.start_date == TODAY
    assert playthrough.completion_date == TODAY


def test_status_change_to_completed_keeps_existing_dates():
    playthrough = Playthrough("PC", "completed", 10, "2026-01-01", "2026-02-01")

    apply_status_change(playthrough, "completed", TODAY)

    assert playthrough.start_date == "2026-01-01"
    assert playthrough.completion_date == "2026-02-01"


def test_date_order_is_valid_when_a_date_is_missing():
    assert is_valid_date_order(None, "2026-01-01")
    assert is_valid_date_order("2026-01-01", None)


def test_date_order_accepts_same_day():
    assert is_valid_date_order("2026-01-01", "2026-01-01")


def test_date_order_rejects_completion_before_start():
    assert not is_valid_date_order("2026-02-01", "2026-01-01")


def test_platform_spelling_reuses_existing_one():
    games = [Game("Hades", 9, [Playthrough("PS4", "completed", 40)])]

    assert find_platform_spelling(games, "ps4") == "PS4"


def test_platform_spelling_keeps_new_platform_as_typed():
    games = [Game("Hades", 9, [Playthrough("PS4", "completed", 40)])]

    assert find_platform_spelling(games, "Switch") == "Switch"


def test_summary_status_prefers_playing_over_completed():
    game = make_game("Hades", make_playthrough("completed"), make_playthrough("playing"))

    assert summary_status(game) == "playing"


def test_summary_status_of_game_without_playthroughs_is_backlog():
    assert summary_status(make_game("Hades")) == BACKLOG


def test_filter_games_by_title_ignores_case_and_spaces():
    games = [make_game("Hades"), make_game("Celeste")]

    assert filter_games(games, "  HAD ") == [games[0]]


def test_filter_games_combines_title_and_status():
    games = [
        make_game("Zelda: Ocarina", make_playthrough("playing")),
        make_game("Zelda: Breath", make_playthrough("completed")),
        make_game("Hades", make_playthrough("playing")),
    ]

    assert filter_games(games, "zelda", "playing") == [games[0]]


def test_count_by_summary_status_includes_empty_statuses():
    games = [make_game("Hades", make_playthrough("completed")), make_game("Celeste")]

    assert count_by_summary_status(games) == {"playing": 0, "completed": 1, "dropped": 0, BACKLOG: 1}


def test_playthrough_statuses_lists_each_status_once_in_priority_order():
    game = make_game(
        "Hades",
        make_playthrough("dropped"),
        make_playthrough("completed"),
        make_playthrough("completed"),
    )

    assert playthrough_statuses(game) == ["completed", "dropped"]


def test_playthrough_statuses_is_empty_for_backlog_game():
    assert playthrough_statuses(make_game("Hades")) == []


def test_rating_must_be_a_whole_number_from_1_to_5():
    assert is_valid_rating(1)
    assert is_valid_rating(5)
    assert not is_valid_rating(3.5)
    assert not is_valid_rating(0)
    assert not is_valid_rating(6)


def test_known_platforms_lists_each_platform_once_in_alphabetical_order():
    games = [
        make_game("Hades", Playthrough("Switch", "completed", 10), Playthrough("PC", "dropped", 2)),
        make_game("Celeste", Playthrough("PC", "completed", 8)),
        make_game("GTA VI"),
    ]

    assert known_platforms(games) == ["PC", "Switch"]


def test_validate_new_playthrough_requires_hours_when_completed():
    error = validate_new_playthrough("completed", 0, "2026-01-01", "2026-01-02")

    assert error == "Una partita completata deve avere delle ore."


def test_validate_new_playthrough_rejects_completion_before_start():
    error = validate_new_playthrough("completed", 10, "2026-02-01", "2026-01-01")

    assert error == "La data di completamento non può precedere la data di inizio."


def test_validate_new_playthrough_accepts_playing_with_zero_hours():
    assert validate_new_playthrough("playing", 0, "2026-01-01", None) is None


def test_last_activity_date_uses_latest_start_or_completion():
    game = Game("GTA V", playthroughs=[
        Playthrough("PS4", "completed", 100, "2017-12-15", "2018-03-01"),
        Playthrough("PS5", "playing", 5, "2026-10-01"),
    ])

    assert last_activity_date(game) == "2026-10-01"
    assert last_activity_date(Game("Celeste")) is None


def test_recently_played_sorts_by_latest_activity_and_skips_undated():
    old = Game("Vecchio", playthroughs=[Playthrough("PC", "completed", 10, "2020-01-01", "2020-02-01")])
    new = Game("Nuovo", playthroughs=[Playthrough("PC", "playing", 1, "2026-11-01")])
    undated = Game("Senza date", playthroughs=[Playthrough("PC", "playing", 1)])

    assert recently_played([old, undated, new], limit=5) == [new, old]


def test_current_playthrough_is_latest_started_playing_one():
    gta = Game("GTA V", playthroughs=[
        Playthrough("PS4", "completed", 100, "2017-12-15", "2018-03-01"),
        Playthrough("PS5", "playing", 5, "2026-10-01"),
    ])
    zelda = Game("Zelda", playthroughs=[Playthrough("Switch", "playing", 2, "2026-11-05")])

    assert current_playthrough([gta, zelda]) == (zelda, 0)
    assert current_playthrough([Game("Celeste")]) is None
