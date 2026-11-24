import tkinter as tk
from tkinter import messagebox, ttk

from src.core.masking import mask_password, unmask_password
from src.data.errors import DataError
from src.ui.validation import fit_for_display

COPIED_TEXT = "Пароль скопирован. Буфер обмена очистится через 30 секунд."


class DetailsView(ttk.Frame):
    def __init__(self, master, app, entry):
        super().__init__(master, padding=16)
        self._app = app
        self._entry = entry
        self._revealed = False

        ttk.Label(self, text=fit_for_display(entry.service), font=("TkDefaultFont", 14, "bold"),
                  wraplength=700).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        rows = (("Логин", entry.login), ("Адрес (URL)", entry.url), ("Заметка", entry.note))
        row = 1
        for caption, value in rows:
            ttk.Label(self, text=caption).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Label(self, text=fit_for_display(value) or "—", wraplength=420).grid(row=row, column=1, sticky="w", pady=4)
            row += 1

        ttk.Label(self, text="Пароль").grid(row=row, column=0, sticky="w", pady=4)
        self._password_label = ttk.Label(self, font=("TkFixedFont", 11))
        self._password_label.grid(row=row, column=1, sticky="w", pady=4)
        self._reveal_button = ttk.Button(self, text="Показать", command=self._toggle)
        self._reveal_button.grid(row=row, column=2, padx=6)
        row += 1

        self._status = ttk.Label(self, foreground="#2e7d32")
        self._status.grid(row=row, column=0, columnspan=3, sticky="w", pady=6)
        row += 1

        actions = ttk.Frame(self)
        actions.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        ttk.Button(actions, text="Назад", command=app.show_list).pack(side="left")
        ttk.Button(actions, text="Копировать пароль", command=self._copy).pack(side="left", padx=6)
        ttk.Button(actions, text="Изменить", command=lambda: app.show_form(entry.id)).pack(side="right")
        ttk.Button(actions, text="Удалить", command=self._delete).pack(side="right", padx=6)

        self._render_password()

    def _render_password(self):
        if self._revealed:
            self._password_label.config(text=fit_for_display(unmask_password(self._entry.password)))
        else:
            self._password_label.config(text=mask_password(self._entry.password))

    def _toggle(self):
        self._revealed = not self._revealed
        self._reveal_button.config(text="Скрыть" if self._revealed else "Показать")
        self._render_password()

    def _copy(self):
        self._app.clipboard.copy(self._entry.password)
        self._status.config(text=COPIED_TEXT)

    def _delete(self):
        if not messagebox.askyesno("Удаление записи",
                                   f"Удалить запись «{self._entry.service}»? Восстановить её будет нельзя."):
            return
        try:
            self._app.repo.delete(self._entry.id)
        except DataError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self._app.show_list()
