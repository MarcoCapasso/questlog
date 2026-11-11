"""Esegue funzioni lente (come le richieste a IGDB) in background, senza bloccare la finestra."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class TaskSignals(QObject):
    """Segnali con cui un lavoro in background comunica il risultato alla finestra."""

    finished = Signal(object)
    failed = Signal(str)


class BackgroundTask(QRunnable):
    """Un lavoro da eseguire in un thread separato: chiama la funzione e ne emette il risultato o l'errore."""

    def __init__(self, function: Callable[[], Any]) -> None:
        super().__init__()
        self.function = function
        self.signals = TaskSignals()

    def run(self) -> None:
        """Eseguito nel thread in background: non deve mai toccare i widget direttamente."""
        try:
            result = self.function()
        except Exception as error:
            self.signals.failed.emit(str(error))
            return
        self.signals.finished.emit(result)


running_tasks: set[BackgroundTask] = set()


def run_in_background(
    function: Callable[[], Any],
    on_finished: Callable[[Any], None],
    on_failed: Callable[[str], None],
) -> None:
    """Avvia la funzione in background; al termine chiama on_finished o on_failed nel thread della finestra."""
    task = BackgroundTask(function)
    task.setAutoDelete(False)
    task.signals.finished.connect(on_finished)
    task.signals.failed.connect(on_failed)
    task.signals.finished.connect(lambda _result: running_tasks.discard(task))
    task.signals.failed.connect(lambda _message: running_tasks.discard(task))
    running_tasks.add(task)
    QThreadPool.globalInstance().start(task)
