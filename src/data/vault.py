import hmac
import logging
import os
import sqlite3
from pathlib import Path

from src.core.crypto import derive_key, make_verifier
from src.data.db import DEFAULT_DB_PATH, connect
from src.data.errors import (StorageError, ValidationError, VaultAlreadyInitialized,
                             VaultNotInitialized, WrongMasterPassword)
from src.data.repository import EntryRepository

logger = logging.getLogger(__name__)

SALT_SIZE = 16


class Vault:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self._conn = connect(db_path)

    def __enter__(self) -> "Vault":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def is_initialized(self) -> bool:
        return self._read_setting("salt") is not None

    def create(self, master_password: str) -> EntryRepository:
        if not master_password:
            raise ValidationError("Мастер-пароль не может быть пустым.")
        if self.is_initialized():
            raise VaultAlreadyInitialized("Хранилище уже создано. Введите мастер-пароль для входа.")
        salt = os.urandom(SALT_SIZE)
        key = derive_key(master_password, salt)
        try:
            with self._conn:
                self._conn.execute("INSERT INTO settings (key, value) VALUES ('salt', ?)", (salt,))
                self._conn.execute(
                    "INSERT INTO settings (key, value) VALUES ('verifier', ?)", (make_verifier(key),)
                )
        except sqlite3.Error as exc:
            logger.error("Не удалось создать хранилище: %s", exc)
            raise StorageError("Не удалось создать хранилище.") from exc
        logger.info("Хранилище создано")
        return EntryRepository(self._conn, key)

    def unlock(self, master_password: str) -> EntryRepository:
        salt = self._read_setting("salt")
        verifier = self._read_setting("verifier")
        if salt is None or verifier is None:
            raise VaultNotInitialized("Хранилище ещё не создано. Задайте мастер-пароль.")
        key = derive_key(master_password, salt)
        # ключ получаем один раз: core.verify_master вывел бы его повторно (PBKDF2 дорогой)
        if not hmac.compare_digest(make_verifier(key), verifier):
            logger.warning("Неверный мастер-пароль")
            raise WrongMasterPassword("Неверный мастер-пароль.")
        logger.info("Хранилище разблокировано")
        return EntryRepository(self._conn, key)

    def _read_setting(self, name: str) -> bytes | None:
        try:
            row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (name,)).fetchone()
        except sqlite3.Error as exc:
            logger.error("Не удалось прочитать настройку %s: %s", name, exc)
            raise StorageError("Не удалось прочитать данные хранилища.") from exc
        return None if row is None else bytes(row["value"])
