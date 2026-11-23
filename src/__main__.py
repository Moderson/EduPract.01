import sys

from src.data.errors import DataError
from src.data.vault import Vault
from src.ui.app import App


def main() -> int:
    try:
        vault = Vault()
    except DataError as exc:
        print(exc, file=sys.stderr)
        return 1
    App(vault).mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
