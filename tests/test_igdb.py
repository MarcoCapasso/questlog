import pytest
from supabase_functions.errors import FunctionsHttpError

from core.catalog import CatalogGame
from core.igdb import IgdbCatalog, IgdbError, parse_game


def test_parse_game_reads_igdb_fields():
    row = {
        "id": 1942,
        "name": "The Witcher 3: Wild Hunt",
        "cover": {"id": 89386, "image_id": "co1wyy"},
        "first_release_date": 1431993600,
        "platforms": [{"id": 6, "name": "PC (Microsoft Windows)"}],
        "genres": [{"id": 12, "name": "Role-playing (RPG)"}],
        "summary": "Geralt cerca Ciri.",
    }

    game = parse_game(row)

    assert game == CatalogGame(
        igdb_id=1942,
        title="The Witcher 3: Wild Hunt",
        cover_url="https://images.igdb.com/igdb/image/upload/t_cover_big/co1wyy.jpg",
        release_year=2015,
        platforms=["PC"],
        genres=["Role-playing (RPG)"],
        summary="Geralt cerca Ciri.",
    )


def test_parse_game_without_optional_fields():
    game = parse_game({"id": 1, "name": "Gioco misterioso"})

    assert game == CatalogGame(1, "Gioco misterioso")


class FakeFunctions:
    """Imita client.functions: ricorda le richieste e risponde come la Edge Function."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def invoke(self, name, invoke_options):
        self.requests.append((name, invoke_options["body"]))
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, functions):
        self.functions = functions


def test_search_sends_the_action_to_the_edge_function():
    functions = FakeFunctions({"games": [{"id": 1, "name": "Zelda"}]})

    games = IgdbCatalog(FakeClient(functions)).search("zelda")  # type: ignore[arg-type]

    assert functions.requests == [("igdb", {"action": "search", "text": "zelda"})]
    assert [game.title for game in games] == ["Zelda"]


def test_details_returns_none_when_igdb_has_no_game():
    functions = FakeFunctions({"games": []})

    assert IgdbCatalog(FakeClient(functions)).details(999) is None  # type: ignore[arg-type]
    assert functions.requests == [("igdb", {"action": "details", "id": 999})]


def test_unauthorized_becomes_a_login_message():
    functions = FakeFunctions(error=FunctionsHttpError("No credentials", 401))

    with pytest.raises(IgdbError, match="serve il login"):
        IgdbCatalog(FakeClient(functions)).trending()  # type: ignore[arg-type]


def test_function_errors_keep_the_server_message():
    functions = FakeFunctions(error=FunctionsHttpError("IGDB ha risposto con un errore (500).", 502))

    with pytest.raises(IgdbError, match="IGDB ha risposto con un errore"):
        IgdbCatalog(FakeClient(functions)).upcoming()  # type: ignore[arg-type]


def test_parse_game_uses_artwork_as_backdrop_and_lists_screenshots():
    row = {
        "id": 1,
        "name": "Celeste",
        "screenshots": [{"id": 1, "image_id": "sc1"}, {"id": 2, "image_id": "sc2"}],
        "artworks": [{"id": 3, "image_id": "ar1"}],
    }

    game = parse_game(row)

    assert game.screenshot_urls == [
        "https://images.igdb.com/igdb/image/upload/t_screenshot_big/sc1.jpg",
        "https://images.igdb.com/igdb/image/upload/t_screenshot_big/sc2.jpg",
    ]
    assert game.backdrop_url == "https://images.igdb.com/igdb/image/upload/t_1080p/ar1.jpg"
