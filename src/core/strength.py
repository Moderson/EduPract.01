import string

WEAK = "weak"
MEDIUM = "medium"
STRONG = "strong"


def password_strength(password: str) -> str:
    classes = sum([
        any(c in string.ascii_lowercase for c in password),
        any(c in string.ascii_uppercase for c in password),
        any(c in string.digits for c in password),
        any(not c.isalnum() for c in password),
    ])
    length_bonus = (len(password) >= 12) + (len(password) >= 16)
    score = classes + length_bonus if password else 0

    if score <= 2:
        return WEAK
    if score <= 4:
        return MEDIUM
    return STRONG
