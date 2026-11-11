from core.catalog import CatalogGame, FakeCatalog, find_library_game, game_from_catalog
from core.models import Game


def test_fake_catalog_search_ignores_case():
    catalog = FakeCatalog([CatalogGame(1, "Hollow Knight"), CatalogGame(2, "Celeste")])

    results = catalog.search("hollow")

    assert [game.title for game in results] == ["Hollow Knight"]


def test_find_library_game_prefers_igdb_id():
    games = [Game("Titolo cambiato", igdb_id=7), Game("Celeste")]

    found = find_library_game(games, CatalogGame(7, "Celeste"))

    assert found is games[0]


def test_find_library_game_links_by_title_only_if_not_already_linked():
    games = [Game("Celeste", igdb_id=99)]

    assert find_library_game(games, CatalogGame(7, "celeste")) is None
    assert find_library_game([Game("Celeste")], CatalogGame(7, "celeste")) is not None


def test_game_from_catalog_is_a_backlog_game_with_igdb_data():
    game = game_from_catalog(CatalogGame(7, "Celeste", "https://cover.jpg"))

    assert game == Game("Celeste", igdb_id=7, cover_url="https://cover.jpg")


def test_fake_catalog_details_finds_game_by_id():
    catalog = FakeCatalog([CatalogGame(1, "Hollow Knight"), CatalogGame(2, "Celeste")])

    assert catalog.details(2) == CatalogGame(2, "Celeste")
    assert catalog.details(99) is None
