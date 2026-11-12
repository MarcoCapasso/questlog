"""Collegamento a Supabase: client, sessione salvata su disco, login con email o con Google (flusso PKCE).

Si entra in due modi: con Google oppure con email e password. Tutti e due finiscono allo stesso modo:
1. Supabase riceve l'impronta di un segreto PKCE (il segreto vero resta in data/session.json).
2. Ascoltiamo su http://localhost:8765/callback.
3. Il browser torna lì con un codice usa e getta: dopo il login con Google,
   oppure quando clicchi il link di conferma nell'email di registrazione.
4. Scambiamo il codice (più il segreto PKCE) con una sessione, che salviamo su disco.
"""

import json
import re
import threading
import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from supabase import Client, ClientOptions, create_client
from supabase_auth import SyncSupportedStorage
from supabase_auth.errors import AuthError, AuthRetryableError
from supabase_auth.types import AuthResponse, User

from core.storage import DATA_DIR

SESSION_FILE = DATA_DIR / "session.json"
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 8765
CALLBACK_PATH = "/callback"
REDIRECT_URL = f"http://localhost:{CALLBACK_PORT}{CALLBACK_PATH}"
LOGIN_TIMEOUT_SECONDS = 180
CONFIRMATION_TIMEOUT_SECONDS = 15 * 60
CANCEL_CHECK_SECONDS = 0.5
CANCELLED_MESSAGE = "Accesso annullato."
MIN_PASSWORD_LENGTH = 8
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
ERROR_MESSAGES = {
    "invalid_credentials": "Email o password sbagliate.",
    "user_already_exists": "Esiste già un account con questa email: accedi.",
    "email_exists": "Esiste già un account con questa email: accedi.",
    "weak_password": f"Password troppo debole: usa almeno {MIN_PASSWORD_LENGTH} caratteri.",
    "otp_expired": "Il link di conferma è scaduto: fatti mandare un'email nuova.",
    "over_email_send_rate_limit": "Troppe email inviate: riprova tra un po'.",
    "over_request_rate_limit": "Troppi tentativi: riprova tra un po'.",
    "email_address_invalid": "Questo indirizzo email non è valido.",
    "signup_disabled": "La registrazione è disattivata.",
}
SUCCESS_PAGE = """<!doctype html><html lang="it"><meta charset="utf-8"><title>Questlog</title>
<body style="margin:0;height:100vh;display:grid;place-items:center;background:#101214;color:#F1F3F5;
font-family:system-ui,sans-serif;text-align:center"><div><h1 style="font-size:28px">Accesso completato</h1>
<p style="color:#AEB5BD">Puoi chiudere questa scheda e tornare a Questlog: sei già dentro.</p></div></body></html>"""
ERROR_PAGE = SUCCESS_PAGE.replace("Accesso completato", "Accesso non riuscito").replace(
    "Puoi chiudere questa scheda e tornare a Questlog: sei già dentro.", "Torna a Questlog per vedere cosa è successo."
)


class CloudError(Exception):
    """Il collegamento al cloud non è riuscito: login annullato, scaduto o rifiutato."""


@dataclass
class CloudUser:
    """L'utente che ha fatto login, con i dati che servono all'interfaccia."""
    id: str
    email: str
    name: str
    avatar_url: str | None


class FileStorage(SyncSupportedStorage):
    """Dove la libreria supabase salva la sessione: un piccolo file JSON in data/, così il login resta valido.

    Contiene i token di accesso: data/ è esclusa da git, e il file va trattato come una password.
    """

    def __init__(self, path: Path = SESSION_FILE) -> None:
        self.path = path

    def get_item(self, key: str) -> str | None:
        """Restituisce il valore salvato con quella chiave, oppure None."""
        return self.read().get(key)

    def set_item(self, key: str, value: str) -> None:
        """Salva un valore con quella chiave."""
        items = self.read()
        items[key] = value
        self.write(items)

    def remove_item(self, key: str) -> None:
        """Cancella il valore con quella chiave, se c'è."""
        items = self.read()
        if items.pop(key, None) is not None:
            self.write(items)

    def read(self) -> dict[str, str]:
        """Legge tutto il file; se manca o è danneggiato è come se fosse vuoto."""
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                items: dict[str, str] = json.load(file)
            return items
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def write(self, items: dict[str, str]) -> None:
        """Scrive tutto il file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(items, file)


def create_supabase_client(url: str, key: str, storage: SyncSupportedStorage | None = None) -> Client:
    """Crea il client Supabase con il flusso PKCE e la sessione salvata su disco."""
    options = ClientOptions(flow_type="pkce", storage=storage or FileStorage())
    return create_client(url, key, options)


class AuthService:
    """Login, utente attuale e logout, sopra il client Supabase."""

    def __init__(self, client: Client) -> None:
        self.client = client
        self.waiting_cancelled = threading.Event()

    def current_user(self) -> CloudUser | None:
        """Restituisce l'utente della sessione salvata (rinnovandola se serve), oppure None."""
        session = self.client.auth.get_session()
        return to_cloud_user(session.user) if session is not None else None

    def sign_in_with_google(self) -> CloudUser:
        """Fa il login con Google nel browser e restituisce l'utente; blocca finché non finisce.

        Va chiamato in background: può durare quanto ci mette l'utente a scegliere l'account.
        """
        oauth = self.client.auth.sign_in_with_oauth(
            {"provider": "google", "options": {"redirect_to": REDIRECT_URL}}
        )
        return self.wait_for_redirect(oauth.url, LOGIN_TIMEOUT_SECONDS)

    def wait_for_email_confirmation(self) -> CloudUser:
        """Aspetta che l'utente clicchi il link di conferma nell'email; poi è già dentro. Blocca: va in background."""
        return self.wait_for_redirect(None, CONFIRMATION_TIMEOUT_SECONDS)

    def wait_for_redirect(self, login_url: str | None, timeout: float) -> CloudUser:
        """Aspetta il ritorno del browser su localhost e scambia il codice con la sessione."""
        self.waiting_cancelled.clear()
        code = wait_for_login_code(login_url, timeout, self.waiting_cancelled)
        response = call_auth(lambda: self.client.auth.exchange_code_for_session({"auth_code": code}))
        return user_from_response(response)

    def cancel_waiting(self) -> None:
        """Smette di aspettare il browser (login con Google o link di conferma)."""
        self.waiting_cancelled.set()

    def sign_in_with_email(self, email: str, password: str) -> CloudUser | None:
        """Accede con email e password e restituisce l'utente.

        Restituisce None se l'account esiste ma l'email non è ancora confermata.
        """
        try:
            response = self.client.auth.sign_in_with_password({"email": email, "password": password})
        except AuthError as error:
            if error.code == "email_not_confirmed":
                return None
            raise to_cloud_error(error) from error
        return user_from_response(response)

    def sign_up_with_email(self, email: str, password: str) -> CloudUser | None:
        """Crea l'account e fa partire l'email con il link di conferma, che riporta su localhost.

        Restituisce l'utente se Supabase non chiede conferma, altrimenti None: poi si usa wait_for_email_confirmation.
        Chiamata di nuovo su un account non ancora confermato, manda un'email nuova.
        """
        response = call_auth(
            lambda: self.client.auth.sign_up(
                {"email": email, "password": password, "options": {"email_redirect_to": REDIRECT_URL}}
            )
        )
        return user_from_response(response) if response.session is not None else None

    def sign_out(self) -> None:
        """Esce dall'account e cancella la sessione salvata."""
        self.client.auth.sign_out()


def call_auth[T](request: Callable[[], T]) -> T:
    """Esegue una richiesta di login a Supabase; se non va a buon fine, la trasforma in un CloudError in italiano."""
    try:
        return request()
    except AuthError as error:
        raise to_cloud_error(error) from error


def to_cloud_error(error: AuthError) -> CloudError:
    """Traduce un errore della libreria supabase in un CloudError con un messaggio per l'utente."""
    if isinstance(error, AuthRetryableError):
        return CloudError("Supabase non risponde: controlla la connessione e riprova.")
    return CloudError(describe_auth_error(error.code, error.message))


def describe_auth_error(code: str | None, message: str) -> str:
    """Restituisce il messaggio in italiano per un codice di errore di Supabase, oppure quello originale."""
    if code is not None and code in ERROR_MESSAGES:
        return ERROR_MESSAGES[code]
    return f"Supabase ha rifiutato la richiesta: {message}"


def user_from_response(response: AuthResponse) -> CloudUser:
    """Restituisce l'utente di una risposta di login."""
    if response.user is None:
        raise CloudError("Supabase non ha restituito l'utente.")
    return to_cloud_user(response.user)


def validate_credentials(email: str, password: str, confirmation: str | None = None) -> str | None:
    """Controlla email e password prima di mandarle; restituisce cosa c'è che non va, oppure None se vanno bene.

    confirmation è la password ripetuta: si passa solo in registrazione.
    """
    if not EMAIL_PATTERN.fullmatch(email):
        return "Scrivi un indirizzo email valido."
    if confirmation is None:
        return None if password != "" else "Scrivi la password."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"La password deve avere almeno {MIN_PASSWORD_LENGTH} caratteri."
    if password != confirmation:
        return "Le due password non coincidono."
    return None


def to_cloud_user(user: User) -> CloudUser:
    """Ricava dall'utente Supabase i dati per l'interfaccia; nome e foto arrivano dal profilo Google."""
    metadata = user.user_metadata or {}
    email = user.email or ""
    name = metadata.get("full_name") or metadata.get("name") or email.split("@")[0]
    avatar_url = metadata.get("avatar_url") or metadata.get("picture")
    return CloudUser(id=user.id, email=email, name=str(name), avatar_url=avatar_url)


def wait_for_login_code(
    login_url: str | None,
    timeout: float = LOGIN_TIMEOUT_SECONDS,
    cancelled: threading.Event | None = None,
) -> str:
    """Apre il login nel browser e aspetta che torni su localhost con il codice; restituisce il codice.

    Con login_url None non apre niente e aspetta e basta: il link arriva per email.
    Si ferma prima se scade il tempo o se qualcuno imposta l'evento cancelled (il bottone "Annulla").
    """
    result: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        """Risponde all'unica richiesta che ci interessa: il ritorno del browser dopo il login."""

        def do_GET(self) -> None:
            outcome = parse_callback(self.path)
            if outcome is None:
                self.send_response(404)
                self.end_headers()
                return
            result.update(outcome)
            page = SUCCESS_PAGE if "code" in outcome else ERROR_PAGE
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))

        def log_message(self, format: str, *args: object) -> None:
            """Niente log nel terminale a ogni richiesta."""

    try:
        server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), CallbackHandler)
    except OSError as error:
        raise CloudError(f"La porta {CALLBACK_PORT} è occupata: chiudi l'altro programma e riprova.") from error

    deadline = time.monotonic() + timeout
    with server:
        if login_url is not None:
            webbrowser.open(login_url)
        while not result:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CloudError("Tempo scaduto: l'accesso non è stato completato.")
            if cancelled is not None and cancelled.is_set():
                raise CloudError(CANCELLED_MESSAGE)
            server.timeout = min(remaining, CANCEL_CHECK_SECONDS)
            server.handle_request()

    if "code" not in result:
        raise CloudError(f"Login annullato o rifiutato: {result.get('error', 'errore sconosciuto')}.")
    return result["code"]


def parse_callback(path: str) -> dict[str, str] | None:
    """Legge l'indirizzo di ritorno dal login: {"code": ...}, {"error": ...}, oppure None se non è /callback."""
    url = urlparse(path)
    if url.path != CALLBACK_PATH:
        return None
    query = parse_qs(url.query)
    if "code" in query:
        return {"code": query["code"][0]}
    description = query.get("error_description") or query.get("error") or ["errore sconosciuto"]
    return {"error": description[0]}
