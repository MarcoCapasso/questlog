import math

import pandas as pd
import pytest

from analysis import (
    average_rating,
    completion_rate,
    completions_per_year,
    days_to_complete,
    games_to_dataframe,
    hours_by_platform,
    hours_per_game,
    playthroughs_by_status,
)
from models import Game, Playthrough


def make_playthrough(
    status: str = "completed",
    hours_played: float = 10,
    platform: str = "PC",
    start_date: str | None = None,
    completion_date: str | None = None,
) -> Playthrough:
    return Playthrough(platform, status, hours_played, start_date, completion_date)


def make_df(*games: Game) -> pd.DataFrame:
    return games_to_dataframe(list(games))


def test_hours_by_platform_sums_and_sorts_from_most_played():
    df = make_df(
        Game("Hades", 9, [make_playthrough(hours_played=40, platform="PC")]),
        Game("Celeste", 8, [make_playthrough(hours_played=10, platform="Switch")]),
        Game("Zelda", 10, [make_playthrough(hours_played=50, platform="Switch")]),
    )

    result = hours_by_platform(df)

    assert list(result.index) == ["Switch", "PC"]
    assert list(result) == [60, 40]


def test_hours_by_platform_ignores_backlog_games():
    df = make_df(Game("Hades", 9, [make_playthrough(platform="PC")]), Game("GTA VI"))

    assert list(hours_by_platform(df).index) == ["PC"]


def test_playthroughs_by_status_counts_each_playthrough():
    df = make_df(
        Game("Hades", 9, [make_playthrough("completed"), make_playthrough("dropped")]),
        Game("Celeste", None, [make_playthrough("completed")]),
        Game("GTA VI"),
    )

    result = playthroughs_by_status(df)

    assert result["completed"] == 2
    assert result["dropped"] == 1
    assert len(result) == 2


def test_hours_per_game_sums_playthroughs_of_the_same_game():
    df = make_df(Game("GTA V", 8, [make_playthrough(hours_played=2000), make_playthrough(hours_played=100)]))

    assert hours_per_game(df)["GTA V"] == 2100


def test_days_to_complete_counts_days_between_dates():
    df = make_df(Game("Outer Wilds", 10, [make_playthrough(start_date="2026-10-06", completion_date="2026-10-18")]))

    assert list(days_to_complete(df)) == [12]


def test_days_to_complete_skips_unfinished_and_undated_playthroughs():
    df = make_df(
        Game("Hades", 9, [make_playthrough("completed")]),
        Game("Celeste", None, [make_playthrough("playing", start_date="2026-01-01")]),
    )

    assert days_to_complete(df).empty


def test_completions_per_year_is_in_chronological_order():
    df = make_df(
        Game("A", None, [make_playthrough(completion_date="2026-01-10")]),
        Game("B", None, [make_playthrough(completion_date="2026-05-10")]),
        Game("C", None, [make_playthrough(completion_date="2024-03-10")]),
    )

    result = completions_per_year(df)

    assert list(result.index) == [2024, 2026]
    assert list(result) == [1, 2]


def test_completion_rate_ignores_playthroughs_in_progress():
    df = make_df(
        Game("A", None, [make_playthrough("completed"), make_playthrough("completed")]),
        Game("B", None, [make_playthrough("dropped"), make_playthrough("playing")]),
    )

    assert completion_rate(df) == pytest.approx(2 / 3)


def test_completion_rate_is_nan_without_concluded_playthroughs():
    df = make_df(Game("A", None, [make_playthrough("playing")]))

    assert math.isnan(completion_rate(df))


def test_average_rating_counts_each_game_once():
    df = make_df(
        Game("Zelda", 10, [make_playthrough()]),
        Game("GTA V", 8, [make_playthrough(), make_playthrough()]),
    )

    assert average_rating(df) == 9


def test_average_rating_ignores_games_without_rating():
    df = make_df(
        Game("Zelda", 10, [make_playthrough()]),
        Game("Ocarina", None, [make_playthrough("playing")]),
        Game("GTA VI"),
    )

    assert average_rating(df) == 10


def test_average_rating_is_nan_when_no_game_is_rated():
    df = make_df(Game("GTA VI"))

    assert math.isnan(average_rating(df))