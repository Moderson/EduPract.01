import tkinter as tk
from tkinter import messagebox, ttk

from src.core.masking import mask_password
from src.data.errors import DataError

EMPTY_TEXT = "Записей пока нет. Нажмите «Добавить», чтобы сохранить первый пароль."
NOT_FOUND_TEXT = "Ничего не найдено. Измените запрос поиска."
COPIED_TEXT = "Пароль скопирован. Буфер обмена очистится через 30 секунд."


class ListView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=12)
        self._app = app
        self._by_id = {}
        self._query = tk.StringVar()

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Поиск:").pack(side="left")
        ttk.Entry(header, textvariable=self._query, width=32).pack(side="left", padx=6)
        ttk.Button(header, text="Выйти", command=app.lock).pack(side="right")
        self._query.trace_add("write", lambda *_: self.refresh())

        self._tree = ttk.Treeview(self, columns=("service", "login", "password"),
                                  show="headings", selectmode="browse")
        for column, title, width in (("service", "Сервис", 220), ("login", "Логин", 220),
                                     ("password", "Пароль", 160)):
            self._tree.heading(column, text=title)
            self._tree.column(column, width=width, stretch=True)
        self._tree.pack(fill="both", expand=True, pady=8)
        self._tree.bind("<Double-1>", lambda _: self._open())

        self._hint = ttk.Label(self, foreground="#555555", justify="center", wraplength=600)
        self._hint.pack(fill="x")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Добавить", command=app.show_form).pack(side="left")
        ttk.Button(buttons, text="Открыть", command=self._open).pack(side="left", padx=6)
        ttk.Button(buttons, text="Копировать пароль", command=self._copy).pack(side="left")
        ttk.Button(buttons, text="Удалить", command=self._delete).pack(side="right")

        self._status = ttk.Label(self, foreground="#2e7d32")
        self._status.pack(fill="x", pady=(6, 0))
        self.refresh()

    def refresh(self):
        query = self._query.get()
        try:
            matches = self._app.repo.search(query)
        except DataError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self._by_id = {entry.id: entry for entry in matches}
        self._tree.delete(*self._tree.get_children())
        for entry in matches:
            self._tree.insert("", "end", iid=str(entry.id),
                              values=(entry.service, entry.login, mask_password(entry.password)))
        if matches:
            self._hint.config(text="")
        elif query.strip():
            self._hint.config(text=NOT_FOUND_TEXT)
        else:
            self._hint.config(text=EMPTY_TEXT)

    def _selected_entry(self):
        selection = self._tree.selection()
        if not selection:
            messagebox.showinfo("Запись не выбрана", "Выделите запись в списке.")
            return None
        return self._by_id[int(selection[0])]

    def _open(self):
        entry = self._selected_entry()
        if entry is not None:
            self._app.show_details(entry.id)

    def _copy(self):
        entry = self._selected_entry()
        if entry is None:
            return
        self._app.clipboard.copy(entry.password)
        self._status.config(text=COPIED_TEXT)

    def _delete(self):
        entry = self._selected_entry()
        if entry is None:
            return
        if not messagebox.askyesno("Удаление записи",
                                   f"Удалить запись «{entry.service}»? Восстановить её будет нельзя."):
            return
        try:
            self._app.repo.delete(entry.id)
        except DataError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self._status.config(text=f"Запись «{entry.service}» удалена.")
        self.refresh()
