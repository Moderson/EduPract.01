import tkinter as tk
from tkinter import messagebox, ttk

from src.core.generator import generate_password
from src.core.models import Entry
from src.core.strength import password_strength
from src.data.errors import DataError
from src.ui.validation import parse_length, validate_entry, validate_generator_sets

ERROR_COLOR = "#b00020"
STRENGTH_TEXT = {"weak": "слабый", "medium": "средний", "strong": "сильный"}
FIELDS = ("service", "login", "password", "url", "note")
SETS = (("lower", "строчные", True), ("upper", "заглавные", True),
        ("digits", "цифры", True), ("specials", "спецсимволы", False))


class EntryForm(ttk.Frame):
    def __init__(self, master, app, entry=None):
        super().__init__(master, padding=16)
        self._app = app
        self._entry_id = None if entry is None else entry.id
        source = entry if entry is not None else Entry()
        self._vars = {name: tk.StringVar(value=getattr(source, name)) for name in FIELDS}
        self._error_labels = {}
        self._sets = {}
        self._row = 1

        title = "Изменение записи" if entry is not None else "Новая запись"
        ttk.Label(self, text=title, font=("TkDefaultFont", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self._add_entry_row("Сервис *", "service")
        self._add_entry_row("Логин", "login")
        self._add_password_row()
        self._add_generator_row()
        self._add_entry_row("Адрес (URL)", "url")
        self._add_entry_row("Заметка", "note")

        actions = ttk.Frame(self)
        actions.grid(row=self._row, column=0, columnspan=3, sticky="e", pady=(16, 0))
        ttk.Button(actions, text="Отмена", command=self._cancel).pack(side="right")
        ttk.Button(actions, text="Сохранить", command=self._save).pack(side="right", padx=6)

        self._update_strength()

    def _add_entry_row(self, caption, name):
        ttk.Label(self, text=caption).grid(row=self._row, column=0, sticky="w", pady=2)
        ttk.Entry(self, textvariable=self._vars[name], width=40).grid(
            row=self._row, column=1, columnspan=2, sticky="ew", pady=2)
        self._row += 1
        self._add_error_label(name)

    def _add_password_row(self):
        ttk.Label(self, text="Пароль *").grid(row=self._row, column=0, sticky="w", pady=2)
        self._password_entry = ttk.Entry(self, textvariable=self._vars["password"], width=40, show="•")
        self._password_entry.grid(row=self._row, column=1, sticky="ew", pady=2)
        self._reveal = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Показать", variable=self._reveal,
                        command=self._toggle_reveal).grid(row=self._row, column=2, sticky="w", padx=6)
        self._row += 1
        self._strength = ttk.Label(self)
        self._strength.grid(row=self._row, column=1, sticky="w")
        self._row += 1
        self._add_error_label("password")
        self._vars["password"].trace_add("write", lambda *_: self._update_strength())

    def _add_generator_row(self):
        ttk.Label(self, text="Генератор").grid(row=self._row, column=0, sticky="w", pady=2)
        box = ttk.Frame(self)
        box.grid(row=self._row, column=1, columnspan=2, sticky="w", pady=2)
        self._length = tk.StringVar(value="16")
        ttk.Label(box, text="длина").pack(side="left")
        ttk.Spinbox(box, from_=8, to=64, width=4, textvariable=self._length).pack(side="left", padx=4)
        for key, caption, default in SETS:
            var = tk.BooleanVar(value=default)
            self._sets[key] = var
            ttk.Checkbutton(box, text=caption, variable=var).pack(side="left", padx=2)
        ttk.Button(box, text="Сгенерировать", command=self._generate).pack(side="left", padx=6)
        self._row += 1
        self._generator_error = ttk.Label(self, foreground=ERROR_COLOR)
        self._generator_error.grid(row=self._row, column=1, columnspan=2, sticky="w")
        self._row += 1

    def _add_error_label(self, name):
        label = ttk.Label(self, foreground=ERROR_COLOR)
        label.grid(row=self._row, column=1, columnspan=2, sticky="w")
        self._error_labels[name] = label
        self._row += 1

    def _toggle_reveal(self):
        self._password_entry.config(show="" if self._reveal.get() else "•")

    def _update_strength(self):
        password = self._vars["password"].get()
        if not password:
            self._strength.config(text="")
            return
        level = password_strength(password)
        self._strength.config(text=f"Надёжность: {STRENGTH_TEXT[level]}")

    def _generate(self):
        length, error = parse_length(self._length.get())
        if error is None:
            error = validate_generator_sets(*(var.get() for var in self._sets.values()))
        self._generator_error.config(text=error or "")
        if error is None:
            self._vars["password"].set(generate_password(length, *(var.get() for var in self._sets.values())))

    def _save(self):
        service = self._vars["service"].get().strip()
        password = self._vars["password"].get()
        errors = validate_entry(service, password)
        for name, label in self._error_labels.items():
            label.config(text=errors.get(name, ""))
        if errors:
            return
        entry = Entry(
            id=self._entry_id,
            service=service,
            login=self._vars["login"].get().strip(),
            password=password,
            url=self._vars["url"].get().strip(),
            note=self._vars["note"].get().strip(),
        )
        try:
            if self._entry_id is None:
                self._app.repo.add(entry)
            else:
                self._app.repo.update(entry)
        except DataError as exc:
            messagebox.showerror("Не удалось сохранить", str(exc))
            return
        self._back()

    def _cancel(self):
        self._back()

    def _back(self):
        if self._entry_id is None:
            self._app.show_list()
        else:
            self._app.show_details(self._entry_id)
