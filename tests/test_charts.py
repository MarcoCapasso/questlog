import pandas as pd
from matplotlib.colors import to_hex

from core.charts import (
    COMPLETIONS_CHART_FILE,
    LIGHT_THEME,
    HOURS_HISTOGRAM_FILE,
    PLATFORM_CHART_FILE,
    STATUS_CHART_FILE,
    create_status_figure,
    save_completions_chart,
    save_hours_by_platform_chart,
    save_hours_histogram,
    save_status_chart,
)


def test_charts_are_saved_as_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    platform_hours = pd.Series({"PC": 40.0, "Switch": 10.0})
    status_counts = pd.Series({"completed": 2, "playing": 1})
    game_hours = pd.Series({"Hades": 40.0, "Celeste": 10.0})
    year_completions = pd.Series({2025: 1, 2026: 2})

    save_hours_by_platform_chart(platform_hours)
    save_status_chart(status_counts)
    save_hours_histogram(game_hours, 25.0)
    save_completions_chart(year_completions)

    for chart_file in [PLATFORM_CHART_FILE, STATUS_CHART_FILE, HOURS_HISTOGRAM_FILE, COMPLETIONS_CHART_FILE]:
        assert (tmp_path / chart_file).exists()

def test_figures_use_the_theme_background_and_italian_statuses():
    figure = create_status_figure(pd.Series({"completed": 2, "playing": 1}), LIGHT_THEME)

    assert to_hex(figure.get_facecolor()) == LIGHT_THEME.background.lower()
    assert [tick.get_text() for tick in figure.axes[0].get_xticklabels()] == ["Completate", "In corso"]
