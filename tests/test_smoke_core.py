import os

import pytest
from cryptography.fernet import InvalidToken

from src.core.crypto import (decrypt_password, derive_key, encrypt_password,
                             make_verifier, verify_master)
from src.core.generator import SYMBOL_SETS, generate_password
from src.core.masking import MASK, mask_password
from src.core.models import Entry
from src.core.search import filter_entries
from src.core.strength import password_strength


@pytest.mark.parametrize("length", [8, 16, 64])
def test_generator_length(length):
    assert len(generate_password(length)) == length


@pytest.mark.parametrize("length", [7, 65])
def test_generator_length_out_of_range(length):
    with pytest.raises(ValueError):
        generate_password(length)


def test_generator_no_sets_selected():
    with pytest.raises(ValueError, match="хотя бы один набор"):
        generate_password(12, False, False, False, False)


def test_generator_only_digits():
    assert generate_password(20, False, False, True, False).isdigit()


def test_generator_contains_every_selected_set():
    for _ in range(50):
        pwd = generate_password(8, True, True, True, True)
        for charset in SYMBOL_SETS.values():
            assert any(c in charset for c in pwd)


def test_strength_levels():
    assert password_strength("abc") == "weak"
    assert password_strength("Password1") == "medium"
    assert password_strength("Xk9#mQ2$vLp7!zRt") == "strong"


def test_mask_is_fixed_length():
    assert mask_password("a") == MASK == mask_password("very long password 123")
    assert len(MASK) == 8


def test_search_case_insensitive_service_and_login():
    entries = [Entry(1, "GitHub", "alice"), Entry(2, "Mail", "Bob")]
    assert [e.id for e in filter_entries(entries, "github")] == [1]
    assert [e.id for e in filter_entries(entries, "BOB")] == [2]
    assert len(filter_entries(entries, "")) == 2
    assert filter_entries(entries, "zzz") == []


def test_master_password_verification():
    salt = os.urandom(16)
    verifier = make_verifier(derive_key("master", salt))
    assert verify_master("master", salt, verifier)
    assert not verify_master("wrong", salt, verifier)


def test_encrypt_roundtrip_and_not_plaintext():
    key = derive_key("master", b"0123456789abcdef")
    token = encrypt_password("s3cret!", key)
    assert "s3cret" not in token
    assert decrypt_password(token, key) == "s3cret!"


def test_decrypt_with_wrong_key_fails():
    token = encrypt_password("s3cret!", derive_key("a", b"0123456789abcdef"))
    with pytest.raises(InvalidToken):
        decrypt_password(token, derive_key("b", b"0123456789abcdef"))
