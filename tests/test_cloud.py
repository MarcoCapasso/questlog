import threading
import urllib.request

import pytest
from supabase_auth.types import User

from core import cloud
from core.cloud import (
    CloudError,
    FileStorage,
    describe_auth_error,
    parse_callback,
    to_cloud_user,
    validate_credentials,
    wait_for_login_code,
)


def test_parse_callback_reads_code_or_error():
    assert parse_callback("/callback?code=abc123") == {"code": "abc123"}
    assert parse_callback("/callback?error=access_denied&error_description=Annullato") == {"error": "Annullato"}
    assert parse_callback("/favicon.ico") is None


def test_file_storage_keeps_values_between_instances(tmp_path):
    path = tmp_path / "session.json"
    FileStorage(path).set_item("token", "segreto")

    storage = FileStorage(path)

    assert storage.get_item("token") == "segreto"
    storage.remove_item("token")
    assert FileStorage(path).get_item("token") is None


def test_file_storage_with_damaged_file_is_empty(tmp_path):
    path = tmp_path / "session.json"
    path.write_text("non è json", encoding="utf-8")

    assert FileStorage(path).get_item("token") is None


def test_to_cloud_user_uses_google_profile():
    user = User(
        id="u1",
        app_metadata={},
        user_metadata={"full_name": "Marco Rossi", "avatar_url": "https://foto.jpg"},
        aud="authenticated",
        created_at="2026-11-12T10:00:00Z",
        email="marco@example.com",
    )

    assert to_cloud_user(user) == cloud.CloudUser("u1", "marco@example.com", "Marco Rossi", "https://foto.jpg")


def fake_browser(path):
    """Simula il browser che, dopo il login, torna su localhost all'indirizzo indicato."""
    def open_url(_url):
        address = f"http://{cloud.CALLBACK_HOST}:{cloud.CALLBACK_PORT}"
        no_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        thread = threading.Thread(target=lambda: no_proxy.open(f"{address}{path}").read())
        thread.start()
        return True
    return open_url


def test_wait_for_login_code_receives_the_code(monkeypatch):
    monkeypatch.setattr(cloud.webbrowser, "open", fake_browser("/callback?code=xyz"))

    assert wait_for_login_code("https://login") == "xyz"


def test_wait_for_login_code_reports_refused_login(monkeypatch):
    monkeypatch.setattr(cloud.webbrowser, "open", fake_browser("/callback?error=access_denied"))

    with pytest.raises(CloudError, match="access_denied"):
        wait_for_login_code("https://login")


def test_wait_for_login_code_times_out(monkeypatch):
    monkeypatch.setattr(cloud.webbrowser, "open", lambda _url: True)

    with pytest.raises(CloudError, match="Tempo scaduto"):
        wait_for_login_code("https://login", timeout=0.2)


def test_validate_credentials_for_sign_in():
    assert validate_credentials("marco@example.com", "qualsiasi") is None
    assert validate_credentials("marco", "password") == "Scrivi un indirizzo email valido."
    assert validate_credentials("marco@example.com", "") == "Scrivi la password."


def test_validate_credentials_for_sign_up():
    assert validate_credentials("marco@example.com", "lunga1234", "lunga1234") is None
    assert validate_credentials("marco@example.com", "corta", "corta") == "La password deve avere almeno 8 caratteri."
    assert validate_credentials("marco@example.com", "lunga1234", "lunga9999") == "Le due password non coincidono."


def test_describe_auth_error_translates_known_codes():
    assert describe_auth_error("invalid_credentials", "Invalid login credentials") == "Email o password sbagliate."
    assert describe_auth_error(None, "Boom") == "Supabase ha rifiutato la richiesta: Boom"


def test_wait_for_login_code_stops_when_cancelled(monkeypatch):
    monkeypatch.setattr(cloud.webbrowser, "open", lambda _url: True)
    cancelled = threading.Event()
    cancelled.set()

    with pytest.raises(CloudError, match="annullato"):
        wait_for_login_code("https://login", timeout=5, cancelled=cancelled)


def test_wait_for_login_code_without_url_only_listens(monkeypatch):
    def fail_if_opened(_url):
        raise AssertionError("Con il link via email il browser non va aperto")
    monkeypatch.setattr(cloud.webbrowser, "open", fail_if_opened)
    click_link = fake_browser("/callback?code=dall-email")
    timer = threading.Timer(0.3, click_link, args=["(link nell'email)"])
    timer.start()

    assert wait_for_login_code(None, timeout=5) == "dall-email"
