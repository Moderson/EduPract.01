from src.core.generator import MAX_LENGTH, MIN_LENGTH


def validate_service(service: str) -> str | None:
    if not service.strip():
        return "Укажите название сервиса."
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "Введите пароль."
    return None


def validate_master(master: str) -> str | None:
    if not master:
        return "Введите мастер-пароль."
    return None


def validate_master_confirmation(master: str, confirmation: str) -> str | None:
    if master != confirmation:
        return "Пароли не совпадают."
    return None


def parse_length(text: str) -> tuple[int | None, str | None]:
    try:
        value = int(text)
    except ValueError:
        return None, "Длина должна быть целым числом."
    if not MIN_LENGTH <= value <= MAX_LENGTH:
        return None, f"Длина пароля от {MIN_LENGTH} до {MAX_LENGTH} символов."
    return value, None


def validate_generator_sets(lower: bool, upper: bool, digits: bool, specials: bool) -> str | None:
    if not any((lower, upper, digits, specials)):
        return "Выберите хотя бы один набор символов."
    return None


def validate_entry(service: str, password: str) -> dict[str, str]:
    errors = {}
    service_error = validate_service(service)
    if service_error is not None:
        errors["service"] = service_error
    password_error = validate_password(password)
    if password_error is not None:
        errors["password"] = password_error
    return errors
