import pytest
from postgrest.exceptions import APIError

from core.cloud import CloudError
from core.cloud_repository import SupabaseGameRepository, game_from_row, game_to_row
from core.models import Game, Playthrough


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    """Imita le richieste del client supabase: si concatenano i metodi e alla fine execute()."""

    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error

    def select(self, _columns):
        return self

    def execute(self):
        if self.error is not None:
            raise self.error
        return FakeResponse(self.data)


class FakeClient:
    def __init__(self, rows=None, error=None):
        self.rows = rows
        self.error = error
        self.rpc_calls = []

    def table(self, name):
        assert name == "games"
        return FakeQuery(self.rows, self.error)

    def rpc(self, name, params):
        self.rpc_calls.append((name, params))
        return FakeQuery([], self.error)


def make_game():
    return Game(
        title="Hades",
        rating=5,
        playthroughs=[
            Playthrough("PC", "completed", 40.5, "2026-01-01", "2026-02-01", "Finale vero"),
            Playthrough("Switch", "playing", 3.0),
        ],
        igdb_id=113112,
        cover_url="https://copertina.jpg",
    )


def test_game_to_row_and_back_gives_the_same_game():
    row = game_to_row(make_game())
    row["position"] = 0
    for position, playthrough in enumerate(row["playthroughs"]):
        playthrough["position"] = position

    assert game_from_row(row) == make_game()


def test_game_from_row_orders_playthroughs_by_position():
    row = {
        "title": "Celeste", "rating": None, "igdb_id": None, "cover_url": None, "position": 0,
        "playthroughs": [
            {"platform": "Switch", "status": "playing", "hours_played": 2, "start_date": None,
             "completion_date": None, "notes": "", "position": 1},
            {"platform": "PC", "status": "dropped", "hours_played": 1, "start_date": None,
             "completion_date": None, "notes": "", "position": 0},
        ],
    }

    game = game_from_row(row)

    assert [playthrough.platform for playthrough in game.playthroughs] == ["PC", "Switch"]
    assert game.playthroughs[1].hours_played == 2.0


def test_fetch_games_keeps_the_saved_order():
    rows = [
        {"title": "B", "rating": None, "igdb_id": None, "cover_url": None, "position": 1, "playthroughs": []},
        {"title": "A", "rating": 4, "igdb_id": None, "cover_url": None, "position": 0, "playthroughs": []},
    ]

    games = SupabaseGameRepository(FakeClient(rows)).fetch_games()  # type: ignore[arg-type]

    assert [game.title for game in games] == ["A", "B"]


def test_upload_games_sends_the_whole_library_to_replace_library():
    client = FakeClient()

    SupabaseGameRepository(client).upload_games([make_game()])  # type: ignore[arg-type]

    name, params = client.rpc_calls[0]
    assert name == "replace_library"
    assert params["library"][0]["title"] == "Hades"
    assert len(params["library"][0]["playthroughs"]) == 2


def test_database_errors_become_cloud_errors():
    error = APIError({"message": "permission denied", "code": "42501"})
    repository = SupabaseGameRepository(FakeClient(error=error))  # type: ignore[arg-type]

    with pytest.raises(CloudError, match="Non riesco a leggere la libreria online"):
        repository.fetch_games()
