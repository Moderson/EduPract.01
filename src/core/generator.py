import secrets
import string

MIN_LENGTH = 8
MAX_LENGTH = 64

SYMBOL_SETS = {
    "lower": string.ascii_lowercase,
    "upper": string.ascii_uppercase,
    "digits": string.digits,
    "specials": "!@#$%^&*()-_=+[]{};:,.?",
}


def generate_password(length: int = 16, use_lower: bool = True, use_upper: bool = True,
                      use_digits: bool = True, use_specials: bool = False) -> str:
    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise ValueError(f"Длина пароля должна быть от {MIN_LENGTH} до {MAX_LENGTH}")

    flags = {"lower": use_lower, "upper": use_upper, "digits": use_digits, "specials": use_specials}
    selected = [SYMBOL_SETS[name] for name, enabled in flags.items() if enabled]
    if not selected:
        raise ValueError("Выберите хотя бы один набор символов")

    chars = [secrets.choice(charset) for charset in selected]
    pool = "".join(selected)
    chars += [secrets.choice(pool) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)
