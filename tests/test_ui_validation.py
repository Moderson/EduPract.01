import pytest

from src.core.generator import MAX_LENGTH, MIN_LENGTH
from src.ui.validation import (parse_length, validate_entry, validate_generator_sets,
                               validate_master, validate_master_confirmation,
                               validate_password, validate_service)


@pytest.mark.parametrize("service", ["", "   ", "\t"])
def test_service_required(service):
    assert validate_service(service) == "Укажите название сервиса."


def test_service_filled():
    assert validate_service("GitHub") is None


def test_password_required():
    assert validate_password("") == "Введите пароль."
    assert validate_password("x") is None


def test_master_required():
    assert validate_master("") == "Введите мастер-пароль."
    assert validate_master("master") is None


def test_master_confirmation_mismatch():
    assert validate_master_confirmation("abc", "abd") == "Пароли не совпадают."
    assert validate_master_confirmation("abc", "abc") is None


@pytest.mark.parametrize("text", [str(MIN_LENGTH), str(MAX_LENGTH), "16"])
def test_length_in_range_accepted(text):
    value, error = parse_length(text)
    assert value == int(text)
    assert error is None


@pytest.mark.parametrize("text", [str(MIN_LENGTH - 1), str(MAX_LENGTH + 1), "0", "-5"])
def test_length_out_of_range_rejected(text):
    value, error = parse_length(text)
    assert value is None
    assert str(MIN_LENGTH) in error and str(MAX_LENGTH) in error


@pytest.mark.parametrize("text", ["", "abc", "12.5", " "])
def test_length_not_a_number_rejected(text):
    value, error = parse_length(text)
    assert value is None
    assert error == "Длина должна быть целым числом."


def test_no_generator_sets_rejected():
    assert validate_generator_sets(False, False, False, False) == "Выберите хотя бы один набор символов."
    assert validate_generator_sets(False, False, True, False) is None


def test_validate_entry_reports_all_fields():
    assert validate_entry("", "") == {
        "service": "Укажите название сервиса.",
        "password": "Введите пароль.",
    }


def test_validate_entry_valid_returns_empty():
    assert validate_entry("GitHub", "Secret1!") == {}
