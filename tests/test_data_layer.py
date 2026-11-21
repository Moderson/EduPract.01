import sqlite3
import time

import pytest

from src.core.models import Entry
from src.data.db import connect
from src.data.errors import (EntryNotFound, StorageError, ValidationError,
                             VaultAlreadyInitialized, VaultNotInitialized,
                             WrongMasterPassword)
from src.data.vault import Vault

MASTER = "test-master-password"
SECRET = "S3cretPassw0rd!Zq"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "vault.db"


@pytest.fixture
def repo(db_path):
    with Vault(db_path) as vault:
        yield vault.create(MASTER)


def make_entry(**kwargs):
    data = dict(service="GitHub", login="alice", password=SECRET, url="https://github.com", note="work")
    data.update(kwargs)
    return Entry(**data)


def test_add_and_get_roundtrip(repo):
    saved = repo.add(make_entry())
    assert saved.id is not None
    assert repo.get(saved.id) == saved


def test_data_survives_restart(db_path):
    with Vault(db_path) as vault:
        vault.create(MASTER).add(make_entry())
    with Vault(db_path) as vault:
        entries = vault.unlock(MASTER).list_all()
    assert [(e.service, e.login, e.password) for e in entries] == [("GitHub", "alice", SECRET)]


def test_password_not_in_database_file(db_path):
    with Vault(db_path) as vault:
        vault.create(MASTER).add(make_entry())
    raw = db_path.read_bytes()
    assert SECRET.encode() not in raw
    assert MASTER.encode() not in raw


def test_update_changes_fields_and_reencrypts(repo):
    saved = repo.add(make_entry())
    repo.update(Entry(saved.id, "GitLab", "bob", "NewPassw0rd!Xy", "", ""))
    got = repo.get(saved.id)
    assert (got.service, got.login, got.password) == ("GitLab", "bob", "NewPassw0rd!Xy")


def test_delete_removes_entry(repo):
    saved = repo.add(make_entry())
    repo.delete(saved.id)
    assert repo.list_all() == []
    with pytest.raises(EntryNotFound):
        repo.get(saved.id)


def test_empty_storage_returns_empty_list(repo):
    assert repo.list_all() == []
    assert repo.search("anything") == []


def test_search_by_service_and_login_ignores_case(repo):
    repo.add(make_entry(service="GitHub", login="alice"))
    repo.add(make_entry(service="Mail", login="Bob"))
    assert [e.service for e in repo.search("github")] == ["GitHub"]
    assert [e.service for e in repo.search("BOB")] == ["Mail"]
    assert len(repo.search("")) == 2


def test_search_cyrillic_ignores_case(repo):
    repo.add(make_entry(service="Почта", login="иван"))
    assert len(repo.search("ПОЧТА")) == 1
    assert len(repo.search("ИВАН")) == 1


def test_sql_injection_in_fields_is_stored_as_text(repo):
    nasty = "x'); DROP TABLE entries;--"
    saved = repo.add(make_entry(service=nasty))
    assert repo.get(saved.id).service == nasty
    assert repo.search("drop table")[0].service == nasty


@pytest.mark.parametrize("bad", [
    dict(service=""), dict(service="   "), dict(password=""),
])
def test_add_rejects_invalid_entry(repo, bad):
    with pytest.raises(ValidationError):
        repo.add(make_entry(**bad))
    assert repo.list_all() == []


def test_update_without_id_rejected(repo):
    with pytest.raises(ValidationError):
        repo.update(make_entry())


def test_update_and_delete_missing_entry(repo):
    with pytest.raises(EntryNotFound):
        repo.update(make_entry(id=999))
    with pytest.raises(EntryNotFound):
        repo.delete(999)


def test_wrong_master_password(db_path):
    with Vault(db_path) as vault:
        vault.create(MASTER)
    with Vault(db_path) as vault:
        with pytest.raises(WrongMasterPassword):
            vault.unlock("wrong-password")


def test_unlock_before_create(db_path):
    with Vault(db_path) as vault:
        assert not vault.is_initialized()
        with pytest.raises(VaultNotInitialized):
            vault.unlock(MASTER)


def test_create_twice_rejected(db_path):
    with Vault(db_path) as vault:
        vault.create(MASTER)
        assert vault.is_initialized()
        with pytest.raises(VaultAlreadyInitialized):
            vault.create("another-master")


def test_empty_master_password_rejected(db_path):
    with Vault(db_path) as vault:
        with pytest.raises(ValidationError):
            vault.create("")
        assert not vault.is_initialized()


def test_missing_parent_directory_is_created(tmp_path):
    path = tmp_path / "new" / "nested" / "vault.db"
    with Vault(path) as vault:
        vault.create(MASTER)
    assert path.exists()


def test_file_that_is_not_a_database(tmp_path):
    bad = tmp_path / "vault.db"
    bad.write_bytes(b"this is definitely not an sqlite database" * 20)
    with pytest.raises(StorageError):
        connect(bad)


def test_path_is_a_directory(tmp_path):
    with pytest.raises(StorageError):
        connect(tmp_path)


def test_tampered_token_is_reported_not_crashing(db_path):
    with Vault(db_path) as vault:
        repo = vault.create(MASTER)
        saved = repo.add(make_entry())
        conn = sqlite3.connect(db_path)
        with conn:
            conn.execute("UPDATE entries SET password = 'garbage' WHERE id = ?", (saved.id,))
        conn.close()
        with pytest.raises(StorageError):
            repo.get(saved.id)


def test_failed_master_attempt_does_not_log_password(db_path, caplog):
    caplog.set_level("DEBUG")
    with Vault(db_path) as vault:
        repo = vault.create(MASTER)
        repo.add(make_entry())
        with pytest.raises(WrongMasterPassword):
            vault.unlock("wrong-password")
        repo.list_all()
    assert SECRET not in caplog.text
    assert MASTER not in caplog.text
    assert "wrong-password" not in caplog.text


def test_search_1000_entries_under_half_second(repo):
    for i in range(1000):
        repo.add(make_entry(service=f"Service{i}", login=f"user{i}"))
    started = time.perf_counter()
    found = repo.search("service99")
    elapsed = time.perf_counter() - started
    assert len(found) == 11
    assert elapsed < 0.5
