import pytest

from src.core.generator import MAX_LENGTH, MIN_LENGTH, SYMBOL_SETS, generate_password
from src.core.models import Entry
from src.core.search import filter_entries
from src.core.strength import password_strength
from src.ui.validation import (DISPLAY_LIMIT, fit_for_display, parse_length,
                               validate_entry)


@pytest.mark.parametrize("password", [
    "a" * 36,
    "abcdefghijklmnopqrstuvwxyz",
    "1234567890123456",
    "",
])
def test_strength_single_class_is_weak(password):
    assert password_strength(password) == "weak"


def test_strength_two_classes_long_is_medium_or_strong():
    assert password_strength("abcDEFGHIJKLMNOPQRSTU") in ("medium", "strong")


def test_strength_mixed_long_is_strong():
    assert password_strength("Xk9#mQ2$vLp7!zRt") == "strong"


@pytest.mark.parametrize("length", [MIN_LENGTH, 16, MAX_LENGTH])
def test_generator_returns_requested_length(length):
    assert len(generate_password(length)) == length


def test_generator_contains_one_char_from_each_selected_set():
    for _ in range(30):
        pwd = generate_password(8, True, True, True, True)
        for charset in SYMBOL_SETS.values():
            assert any(c in charset for c in pwd)


def test_generator_uses_only_selected_sets():
    pwd = generate_password(32, use_lower=False, use_upper=False, use_digits=True, use_specials=False)
    assert set(pwd) <= set(SYMBOL_SETS["digits"])


@pytest.mark.parametrize("length", [MIN_LENGTH - 1, MAX_LENGTH + 1])
def test_generator_rejects_length_out_of_range(length):
    with pytest.raises(ValueError):
        generate_password(length)


def test_generator_rejects_no_sets():
    with pytest.raises(ValueError):
        generate_password(12, False, False, False, False)


ENTRIES = [
    Entry(1, "GitHub", "alice"),
    Entry(2, "Почта", "Иван"),
    Entry(3, "Bank", "bob@example.com"),
]


@pytest.mark.parametrize("query, expected_ids", [
    ("git", [1]),
    ("GIT", [1]),
    ("ALICE", [1]),
    ("почта", [2]),
    ("иВАН", [2]),
    ("", [1, 2, 3]),
    ("   ", [1, 2, 3]),
    ("nothing", []),
])
def test_filter_entries_matches_service_or_login_case_insensitive(query, expected_ids):
    assert [e.id for e in filter_entries(ENTRIES, query)] == expected_ids


def test_filter_entries_does_not_modify_input():
    original = list(ENTRIES)
    filter_entries(ENTRIES, "git")
    assert ENTRIES == original


@pytest.mark.parametrize("text, value", [("8", 8), ("64", 64), (" 16 ", 16)])
def test_parse_length_accepts_range(text, value):
    assert parse_length(text) == (value, None)


@pytest.mark.parametrize("text", ["7", "65", "0", "-1"])
def test_parse_length_rejects_out_of_range(text):
    value, error = parse_length(text)
    assert value is None and error is not None


@pytest.mark.parametrize("text", ["", "abc", "1.5"])
def test_parse_length_rejects_non_integer(text):
    value, error = parse_length(text)
    assert value is None and error is not None


def test_validate_entry_requires_service_and_password():
    assert validate_entry("  ", "") == {
        "service": "Укажите название сервиса.",
        "password": "Введите пароль.",
    }


def test_validate_entry_accepts_valid_input():
    assert validate_entry("GitHub", "x") == {}


def test_fit_for_display_keeps_short_text():
    assert fit_for_display("короткий") == "короткий"
    assert fit_for_display("a" * DISPLAY_LIMIT) == "a" * DISPLAY_LIMIT


def test_fit_for_display_cuts_long_text_and_reports_size():
    result = fit_for_display("S" * 5000)
    assert result.startswith("S" * DISPLAY_LIMIT)
    assert len(result) < 300
    assert "ещё 4800 симв." in result
