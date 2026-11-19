MASK = "\u2022" * 8


def mask_password(password: str) -> str:
    return MASK if password else ""


def unmask_password(password: str) -> str:
    return password
