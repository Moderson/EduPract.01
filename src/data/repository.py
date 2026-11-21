import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import replace

from cryptography.fernet import InvalidToken

from src.core.crypto import decrypt_password, encrypt_password
from src.core.models import Entry
from src.core.search import filter_entries
from src.data.errors import EntryNotFound, StorageError, ValidationError

logger = logging.getLogger(__name__)

_COLUMNS = "id, service, login, password, url, note"


@contextmanager
def _storage_errors(action: str):
    try:
        yield
    except sqlite3.Error as exc:
        logger.error("Ошибка БД при операции «%s»: %s", action, exc)
        raise StorageError("Ошибка работы с базой данных. Повторите операцию.") from exc


def _validate(entry: Entry) -> None:
    if not entry.service.strip():
        raise ValidationError("Название сервиса не может быть пустым.")
    if not entry.password:
        raise ValidationError("Пароль не может быть пустым.")


def _to_entry(row: sqlite3.Row) -> Entry:
    return Entry(row["id"], row["service"], row["login"], row["password"], row["url"], row["note"])


class EntryRepository:
    def __init__(self, conn: sqlite3.Connection, key: bytes):
        self._conn = conn
        self._key = key

    def add(self, entry: Entry) -> Entry:
        _validate(entry)
        token = encrypt_password(entry.password, self._key)
        with _storage_errors("добавление"), self._conn:
            cur = self._conn.execute(
                "INSERT INTO entries (service, login, password, url, note) VALUES (?, ?, ?, ?, ?)",
                (entry.service, entry.login, token, entry.url, entry.note),
            )
        logger.info("Добавлена запись id=%s", cur.lastrowid)
        return replace(entry, id=cur.lastrowid)

    def get(self, entry_id: int) -> Entry:
        with _storage_errors("чтение"):
            row = self._conn.execute(
                f"SELECT {_COLUMNS} FROM entries WHERE id = ?", (entry_id,)
            ).fetchone()
        if row is None:
            raise EntryNotFound(f"Запись с номером {entry_id} не найдена.")
        return self._decrypt(_to_entry(row))

    def list_all(self) -> list[Entry]:
        return [self._decrypt(e) for e in self._fetch_all()]

    def search(self, query: str) -> list[Entry]:
        return [self._decrypt(e) for e in filter_entries(self._fetch_all(), query)]

    def update(self, entry: Entry) -> None:
        if entry.id is None:
            raise ValidationError("Нельзя изменить запись без номера.")
        _validate(entry)
        token = encrypt_password(entry.password, self._key)
        with _storage_errors("изменение"), self._conn:
            cur = self._conn.execute(
                "UPDATE entries SET service = ?, login = ?, password = ?, url = ?, note = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (entry.service, entry.login, token, entry.url, entry.note, entry.id),
            )
        if cur.rowcount == 0:
            raise EntryNotFound(f"Запись с номером {entry.id} не найдена.")
        logger.info("Изменена запись id=%s", entry.id)

    def delete(self, entry_id: int) -> None:
        with _storage_errors("удаление"), self._conn:
            cur = self._conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        if cur.rowcount == 0:
            raise EntryNotFound(f"Запись с номером {entry_id} не найдена.")
        logger.info("Удалена запись id=%s", entry_id)

    def _fetch_all(self) -> list[Entry]:
        with _storage_errors("чтение списка"):
            rows = self._conn.execute(f"SELECT {_COLUMNS} FROM entries ORDER BY id").fetchall()
        return [_to_entry(r) for r in rows]

    def _decrypt(self, entry: Entry) -> Entry:
        try:
            return replace(entry, password=decrypt_password(entry.password, self._key))
        except InvalidToken as exc:
            logger.error("Не удалось расшифровать запись id=%s", entry.id)
            raise StorageError(
                f"Запись {entry.id} повреждена или зашифрована другим ключом."
            ) from exc
