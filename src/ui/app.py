import tkinter as tk
from tkinter import messagebox, ttk

from src.data.errors import DataError
from src.system.clipboard import ClipboardGuard
from src.ui.details_view import DetailsView
from src.ui.entry_form import EntryForm
from src.ui.list_view import ListView
from src.ui.login_view import LoginView


class App(tk.Tk):
    def __init__(self, vault):
        super().__init__()
        self.title("Менеджер паролей")
        self.geometry("760x520")
        self.minsize(640, 420)
        self._vault = vault
        self._content = None
        self.repo = None
        self.clipboard = ClipboardGuard(self._set_clipboard, self._clear_clipboard, schedule=self._schedule)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.show_login()

    def _set_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _clear_clipboard(self):
        self.clipboard_clear()

    def _schedule(self, delay, callback):
        job = self.after(int(delay * 1000), callback)
        return lambda: self.after_cancel(job)

    def _show(self, frame):
        if self._content is not None:
            self._content.destroy()
        self._content = frame
        self._content.pack(fill="both", expand=True)

    def show_login(self):
        self.repo = None
        self._show(LoginView(self, self._vault, self._on_unlocked))

    def _on_unlocked(self, repo):
        self.repo = repo
        self.show_list()

    def show_list(self):
        self._show(ListView(self, self))

    def show_form(self, entry_id=None):
        entry = None
        if entry_id is not None:
            entry = self._load(entry_id)
            if entry is None:
                return
        self._show(EntryForm(self, self, entry))

    def show_details(self, entry_id):
        entry = self._load(entry_id)
        if entry is None:
            return
        self._show(DetailsView(self, self, entry))

    def _load(self, entry_id):
        try:
            return self.repo.get(entry_id)
        except DataError as exc:
            messagebox.showerror("Ошибка", str(exc))
            self.show_list()
            return None

    def lock(self):
        self.clipboard.clear_now()
        self.show_login()

    def close(self):
        self.clipboard.clear_now()
        self._vault.close()
        self.destroy()
