"""La libreria dell'account: tenuta in memoria per le pagine e salvata online in background."""

from copy import deepcopy
from dataclasses import dataclass

from PySide6.QtCore import QObject, QThreadPool, Signal

from core.cloud import AuthService, CloudError
from core.cloud_repository import SupabaseGameRepository
from core.models import Game
from ui.tasks import run_in_background

FLUSH_TIMEOUT_MS = 10_000


class CloudLibrary(QObject):
    """Un GameRepository come gli altri, ma veloce: le pagine leggono e scrivono una copia in memoria.

    Ogni salvataggio parte verso Supabase in background, uno alla volta e sempre con la libreria più recente,
    così la finestra non si blocca mai ad aspettare la rete.
    """

    sync_failed = Signal(str)

    def __init__(self, remote: SupabaseGameRepository) -> None:
        super().__init__()
        self.remote = remote
        self.games: list[Game] = []
        self.pending: list[Game] | None = None
        self.uploading = False

    def load_games(self) -> list[Game]:
        """Restituisce una copia dei giochi: chi la modifica senza salvare non tocca la libreria."""
        return deepcopy(self.games)

    def save_games(self, games: list[Game]) -> None:
        """Aggiorna subito la copia in memoria e mette in coda il salvataggio online."""
        self.games = deepcopy(games)
        self.pending = deepcopy(games)
        self.start_upload()

    def set_games(self, games: list[Game]) -> None:
        """Usa i giochi appena scaricati da Supabase (dopo il login)."""
        self.games = games
        self.pending = None

    def clear(self) -> None:
        """Dimentica la libreria (dopo il logout): il prossimo account non vede i giochi di questo."""
        self.games = []
        self.pending = None

    def start_upload(self) -> None:
        """Manda online l'ultima libreria in coda, se non c'è già un invio in corso."""
        if self.uploading or self.pending is None:
            return
        games, self.pending = self.pending, None
        self.uploading = True
        run_in_background(lambda: self.remote.upload_games(games), self.on_uploaded, self.on_upload_failed)

    def on_uploaded(self, _result: object) -> None:
        """Invio finito: se nel frattempo sono arrivate altre modifiche, manda anche quelle."""
        self.uploading = False
        self.start_upload()

    def on_upload_failed(self, message: str) -> None:
        """Invio fallito: lo dice e tiene la libreria in coda, così riparte al prossimo salvataggio o all'uscita."""
        self.uploading = False
        if self.pending is None:
            self.pending = deepcopy(self.games)
        self.sync_failed.emit(message)

    def flush(self) -> None:
        """Prima di uscire o di chiudere: aspetta l'invio in corso e manda subito quello in coda.

        Blocca la finestra per un attimo, ma così l'ultima modifica non va persa.
        """
        QThreadPool.globalInstance().waitForDone(FLUSH_TIMEOUT_MS)
        if self.pending is None:
            return
        games, self.pending = self.pending, None
        try:
            self.remote.upload_games(games)
        except CloudError as error:
            self.sync_failed.emit(str(error))


@dataclass
class CloudAccount:
    """Quello che serve alla finestra per l'account online: il login e la libreria."""
    auth: AuthService
    library: CloudLibrary
