from core.models import Game, Playthrough
from core.repository import GameRepository, InMemoryGameRepository, JsonGameRepository


def count_games(repository: GameRepository) -> int:
    return len(repository.load_games())


def test_json_repository_saves_and_loads_games(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repository = JsonGameRepository()
    games = [Game("Hades", 9, [Playthrough("PC", "completed", 40)]), Game("Celeste")]

    repository.save_games(games)

    assert repository.load_games() == games


def test_in_memory_repository_starts_empty():
    assert InMemoryGameRepository().load_games() == []


def test_any_repository_works_where_a_game_repository_is_expected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    in_memory = InMemoryGameRepository([Game("Hades")])
    json_file = JsonGameRepository()

    assert count_games(in_memory) == 1
    assert count_games(json_file) == 0