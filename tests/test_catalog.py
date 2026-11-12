from core.catalog import CatalogGame, FakeCatalog, find_library_game, game_from_catalog, link_library_game
from core.models import Game, Playthrough


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


def test_link_library_game_keeps_playthroughs_and_takes_igdb_title():
    playthrough = Playthrough("PS4", "completed", 100)
    game = Game("zelda botw", 5, [playthrough])

    error = link_library_game([game], game, CatalogGame(7, "The Legend of Zelda: Breath of the Wild", "c.jpg"))

    assert error is None
    assert game == Game("The Legend of Zelda: Breath of the Wild", 5, [playthrough], 7, "c.jpg")


def test_link_library_game_refuses_igdb_game_already_linked_elsewhere():
    linked = Game("Celeste", igdb_id=7)
    game = Game("Celeste (vecchio)")

    error = link_library_game([linked, game], game, CatalogGame(7, "Celeste"))

    assert error is not None
    assert game.igdb_id is None
