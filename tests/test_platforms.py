from core.platforms import normalize_platform, normalize_platforms


def test_aliases_become_the_official_name():
    assert normalize_platform("Ps4") == "PlayStation 4"
    assert normalize_platform("PLAYSTATION 4") == "PlayStation 4"
    assert normalize_platform("PC (Microsoft Windows)") == "PC"
    assert normalize_platform("  switch   2 ") == "Nintendo Switch 2"


def test_unknown_platform_is_kept_without_extra_spaces():
    assert normalize_platform("  Steam   Deck ") == "Steam Deck"


def test_normalize_platforms_removes_duplicates_and_keeps_order():
    assert normalize_platforms(["PS4", "PC (Microsoft Windows)", "PlayStation 4"]) == ["PlayStation 4", "PC"]
