import pytest
import requests

from core.catalog import CatalogGame
from core.igdb import TOKEN_URL, IgdbCatalog, IgdbError, build_search_query, parse_game


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
        platforms=["PC (Microsoft Windows)"],
        genres=["Role-playing (RPG)"],
        summary="Geralt cerca Ciri.",
    )


def test_parse_game_without_optional_fields():
    game = parse_game({"id": 1, "name": "Gioco misterioso"})

    assert game == CatalogGame(1, "Gioco misterioso")


def test_search_query_removes_quotes():
    query = build_search_query('  il "gioco" ')

    assert query.startswith('search "il gioco";')


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        self.ok = status_code < 400

    def json(self):
        return self.data


def test_trending_keeps_popularity_order_and_reuses_token(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        if url == TOKEN_URL:
            return FakeResponse({"access_token": "abc", "expires_in": 3600})
        if url.endswith("/popularity_primitives"):
            return FakeResponse([{"game_id": 2, "value": 0.9}, {"game_id": 1, "value": 0.5}])
        return FakeResponse([{"id": 1, "name": "Primo"}, {"id": 2, "name": "Secondo"}])

    monkeypatch.setattr(requests, "post", fake_post)
    catalog = IgdbCatalog("id", "secret")

    games = catalog.trending()

    assert [game.title for game in games] == ["Secondo", "Primo"]
    assert calls.count(TOKEN_URL) == 1


def test_wrong_credentials_raise_igdb_error(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda url, **kwargs: FakeResponse({}, status_code=400))

    with pytest.raises(IgdbError):
        IgdbCatalog("id", "sbagliato").search("zelda")
