from src.core.models import Entry


def filter_entries(entries: list[Entry], query: str) -> list[Entry]:
    needle = query.strip().casefold()
    if not needle:
        return list(entries)
    return [
        entry for entry in entries
        if needle in entry.service.casefold() or needle in entry.login.casefold()
    ]
