import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30.0


def _timer_schedule(delay: float, callback: Callable[[], None]) -> Callable[[], None]:
    timer = threading.Timer(delay, callback)
    timer.daemon = True
    timer.start()
    return timer.cancel


class ClipboardGuard:
    """Копирует текст в буфер и очищает его через timeout секунд."""

    def __init__(self, set_text: Callable[[str], None], clear: Callable[[], None],
                 timeout: float = DEFAULT_TIMEOUT_SECONDS, schedule=_timer_schedule):
        self._set_text = set_text
        self._clear = clear
        self._timeout = timeout
        self._schedule = schedule
        self._cancel: Callable[[], None] | None = None
        self._lock = threading.Lock()

    def copy(self, text: str) -> None:
        with self._lock:
            self._cancel_pending()
            self._set_text(text)
            self._cancel = self._schedule(self._timeout, self._expire)
        logger.info("Значение скопировано в буфер, очистка через %s с", self._timeout)

    def clear_now(self) -> None:
        with self._lock:
            self._cancel_pending()
            self._clear()

    def _expire(self) -> None:
        with self._lock:
            self._cancel = None
            self._clear()
        logger.info("Буфер обмена очищен по таймеру")

    def _cancel_pending(self) -> None:
        if self._cancel is not None:
            self._cancel()
            self._cancel = None
