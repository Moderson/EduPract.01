from dataclasses import dataclass


@dataclass
class Entry:
    id: int | None = None
    service: str = ""
    login: str = ""
    password: str = ""
    url: str = ""
    note: str = ""
