import json

from core import config


def isolate(monkeypatch, tmp_path, env_text=""):
    """Usa un .env e un file incluso finti, e toglie dall'ambiente le impostazioni vere."""
    env_file = tmp_path / ".env"
    env_file.write_text(env_text, encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.setattr(config, "BUNDLED_SETTINGS_FILE", tmp_path / "app_settings.json")
    for name in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "DEEPL_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_bundled_settings_are_used_when_env_is_missing(monkeypatch, tmp_path):
    isolate(monkeypatch, tmp_path)
    (tmp_path / "app_settings.json").write_text(json.dumps({"SUPABASE_URL": "https://x.supabase.co"}))

    assert config.read_setting("SUPABASE_URL") == "https://x.supabase.co"
    assert config.read_setting("SUPABASE_ANON_KEY") is None


def test_write_bundled_settings_keeps_only_public_settings(monkeypatch, tmp_path):
    isolate(monkeypatch, tmp_path, "SUPABASE_URL=https://x.supabase.co\nDEEPL_API_KEY=segreta\n")
    output = tmp_path / "app_settings.json"

    missing = config.write_bundled_settings(output)

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written == {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_ANON_KEY": ""}
    assert "segreta" not in output.read_text(encoding="utf-8")
    assert missing == ["SUPABASE_ANON_KEY"]
