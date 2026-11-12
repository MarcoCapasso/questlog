from core.models import Game, Playthrough
from core.wrapped import activity_years, compute_wrapped, games_in_year, playthrough_year


def make_library() -> list[Game]:
    return [
        Game("GTA V", 4, [
            Playthrough("PlayStation 4", "completed", 100, "2025-01-01", "2025-01-11"),
            Playthrough("PlayStation 5", "playing", 20, "2026-03-01"),
        ]),
        Game("Outer Wilds", 5, [Playthrough("PC", "completed", 40, "2026-02-01", "2026-02-05")]),
        Game("Celeste"),
    ]


def test_playthrough_year_prefers_completion_date():
    assert playthrough_year(Playthrough("PC", "completed", 1, "2025-12-20", "2026-01-03")) == 2026
    assert playthrough_year(Playthrough("PC", "playing", 1, "2025-12-20")) == 2025
    assert playthrough_year(Playthrough("PC", "playing", 1)) is None


def test_activity_years_from_newest():
    assert activity_years(make_library()) == [2026, 2025]


def test_games_in_year_keeps_only_that_year_and_does_not_touch_the_library():
    library = make_library()

    games = games_in_year(library, 2026)

    assert [game.title for game in games] == ["GTA V", "Outer Wilds"]
    assert len(games[0].playthroughs) == 1
    assert len(library[0].playthroughs) == 2


def test_compute_wrapped_for_all_time():
    stats = compute_wrapped(make_library())

    assert stats.total_hours == 160
    assert stats.games_played == 2
    assert [item.game.title for item in stats.top_games] == ["GTA V", "Outer Wilds"]
    assert stats.platform_hours == [("PlayStation 4", 100), ("PC", 40), ("PlayStation 5", 20)]
    assert (stats.playing, stats.completed, stats.dropped) == (1, 2, 0)
    assert stats.completion_rate == 1
    assert stats.average_rating == 4.5
    assert stats.favorite_game is not None and stats.favorite_game.title == "Outer Wilds"
    assert stats.median_days == 7
    assert stats.fastest is not None and stats.fastest[1] == 4
    assert stats.profile is not None and stats.profile.title == "Il Fedelissimo"


def test_compute_wrapped_without_playthroughs():
    stats = compute_wrapped([Game("Celeste")])

    assert stats.total_hours == 0
    assert stats.top_games == []
    assert stats.completion_rate is None
    assert stats.favorite_game is None
    assert stats.profile is None
