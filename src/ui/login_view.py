from tkinter import ttk

from src.data.errors import DataError
from src.ui.validation import validate_master, validate_master_confirmation

ERROR_COLOR = "#b00020"


class LoginView(ttk.Frame):
    def __init__(self, master, vault, on_unlocked):
        super().__init__(master, padding=32)
        self._vault = vault
        self._on_unlocked = on_unlocked
        self._creating = not vault.is_initialized()

        if self._creating:
            title = "Создание хранилища"
            hint = ("Задайте мастер-пароль. Он нужен для входа в хранилище. "
                    "Восстановить его нельзя, поэтому запомните его.")
        else:
            title = "Вход"
            hint = "Введите мастер-пароль, чтобы открыть хранилище."

        ttk.Label(self, text=title, font=("TkDefaultFont", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(self, text=hint, wraplength=460, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 16))

        ttk.Label(self, text="Мастер-пароль:").grid(row=2, column=0, sticky="w", pady=4)
        self._master = ttk.Entry(self, show="•", width=34)
        self._master.grid(row=2, column=1, sticky="ew", pady=4)
        self._master.bind("<Return>", lambda _: self._submit())
        self._master.focus_set()

        row = 3
        if self._creating:
            ttk.Label(self, text="Повторите пароль:").grid(row=row, column=0, sticky="w", pady=4)
            self._confirm = ttk.Entry(self, show="•", width=34)
            self._confirm.grid(row=row, column=1, sticky="ew", pady=4)
            self._confirm.bind("<Return>", lambda _: self._submit())
            row += 1

        self._error = ttk.Label(self, foreground=ERROR_COLOR, wraplength=460, justify="left")
        self._error.grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(self, text="Создать" if self._creating else "Войти", command=self._submit).grid(
            row=row + 1, column=1, sticky="e", pady=(12, 0))

    def _submit(self):
        master = self._master.get()
        error = validate_master(master)
        if error is None and self._creating:
            error = validate_master_confirmation(master, self._confirm.get())
        if error is not None:
            self._error.config(text=error)
            return
        try:
            repo = self._vault.create(master) if self._creating else self._vault.unlock(master)
        except DataError as exc:
            self._error.config(text=str(exc))
            return
        self._on_unlocked(repo)
