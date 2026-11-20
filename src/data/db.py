import logging
import sqlite3
from pathlib import Path

from src.data.errors import StorageError

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path.home() / ".password_manager" / "vault.db"
BUSY_TIMEOUT_SECONDS = 5

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    service    TEXT NOT NULL,
    login      TEXT NOT NULL DEFAULT '',
    password   TEXT NOT NULL,
    url        TEXT NOT NULL DEFAULT '',
    note       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    conn = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), timeout=BUSY_TIMEOUT_SECONDS)
        conn.row_factory = sqlite3.Row
        with conn:
            conn.executescript(SCHEMA)
    except (OSError, sqlite3.Error) as exc:
        if conn is not None:
            conn.close()
        logger.error("Не удалось открыть базу %s: %s", path, exc)
        raise StorageError(
            "Не удалось открыть файл базы данных. Проверьте путь, права доступа "
            "и что файл не повреждён."
        ) from exc
    logger.info("База открыта: %s", path)
    return conn
