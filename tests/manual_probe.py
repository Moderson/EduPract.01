import json
import os
import time
import tkinter
from tkinter import messagebox

messagebox.showerror = lambda title, message, **kw: SHOWN.append(("error", message))
messagebox.showinfo = lambda title, message, **kw: SHOWN.append(("info", message))
messagebox.askyesno = lambda *a, **kw: ANSWER["yes"]
SHOWN = []
ANSWER = {"yes": True}

from src.core.generator import generate_password
from src.core.models import Entry
from src.core.strength import password_strength
from src.data.vault import Vault
from src.ui.app import App
from src.ui.validation import parse_length

RESULTS = []


def rec(case, status, actual, note=""):
    RESULTS.append({"case": case, "status": status, "actual": str(actual), "note": note})


def settle(app):
    for _ in range(3):
        app.update()
        time.sleep(0.05)


def fill(var_or_entry, text):
    if isinstance(var_or_entry, tkinter.StringVar):
        var_or_entry.set(text)
    else:
        var_or_entry.delete(0, "end")
        var_or_entry.insert(0, text)


def safe(case, fn):
    try:
        fn()
    except Exception as exc:
        rec(case, "Failed", f"исключение: {type(exc).__name__}: {exc}")


app = App(Vault())
settle(app)


def t_empty_create():
    login = app._content
    login._submit()
    rec("P-01 пустой мастер-пароль", "Passed" if login._error.cget("text") == "Введите мастер-пароль." else "Failed",
        login._error.cget("text"))


def t_create():
    login = app._content
    fill(login._master, "Master-1!")
    fill(login._confirm, "Master-1!")
    login._submit()
    settle(app)
    ok = type(app._content).__name__ == "ListView"
    rec("P-02 создание хранилища", "Passed" if ok else "Failed", type(app._content).__name__)


def t_empty_service_and_password():
    app.show_form()
    form = app._content
    form._vars["service"].set("   ")
    form._vars["password"].set("")
    form._save()
    ok = form._error_labels["service"].cget("text") and form._error_labels["password"].cget("text")
    rec("P-03 пробельное название и пустой пароль", "Passed" if ok else "Failed",
        f"service='{form._error_labels['service'].cget('text')}', password='{form._error_labels['password'].cget('text')}'")


def t_long_service():
    form = app._content
    long_name = "S" * 5000
    form._vars["service"].set(long_name)
    form._vars["password"].set("Pass-1!")
    form._save()
    settle(app)
    lst = app._content
    stored = [e for e in app.repo.list_all() if e.service == long_name]
    rec("P-04 название 5000 символов сохраняется", "Passed" if stored else "Failed",
        f"сохранено: {bool(stored)}, окно {app.winfo_width()}x{app.winfo_height()}")
    app._content._tree.selection_set(str(stored[0].id)) if stored else None
    app.show_details(stored[0].id) if stored else None
    settle(app)
    w = app.winfo_reqwidth()
    rec("P-05 длинное название не ломает окно деталей", "Passed" if w <= 1100 else "Failed",
        f"запрошенная ширина окна {w}px при 760px по задумке", note="длинная строка в Label без переноса")
    app.show_list()
    settle(app)


def t_long_password_roundtrip():
    app.show_form()
    form = app._content
    pwd = "Ab1!" * 1250
    form._vars["service"].set("Long")
    form._vars["password"].set(pwd)
    form._save()
    settle(app)
    rec("P-06 пароль 5000 символов", "Passed" if any(e.password == pwd for e in app.repo.list_all()) else "Failed", "round-trip")


def t_unicode_password():
    app.show_form()
    form = app._content
    pwd = "пароль-🔑-密码-Ё!1"
    form._vars["service"].set("Юникод")
    form._vars["password"].set(pwd)
    form._save()
    settle(app)
    rec("P-07 юникод в пароле", "Passed" if any(e.password == pwd for e in app.repo.list_all()) else "Failed", "round-trip")


def t_length_input():
    cases = {"": "err", "abc": "err", "1_6": "accepted", " 16 ": "accepted", "7": "err", "65": "err", "16.0": "err"}
    wrong = []
    for text, expected in cases.items():
        value, error = parse_length(text)
        got = "err" if error else "accepted"
        if got != expected:
            wrong.append(f"'{text}'->{got}")
    rec("P-08 граница и формат длины генератора", "Failed" if wrong else "Passed",
        "; ".join(wrong) or "все проверки верны", note="'1_6' принимается как 16 (int() понимает подчёркивания)")


def t_strength_levels():
    samples = {"1234567890123456": "weak", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "weak", "abc": "weak",
               "Xk9#mQ2$vLp7!zRt": "strong"}
    wrong = {p: password_strength(p) for p, e in samples.items() if password_strength(p) != e}
    rec("P-09 оценка надёжности", "Failed" if wrong else "Passed", wrong or "все уровни верны",
        note="длинная строка из одного класса символов получает 'medium'")


def t_generator_repeat():
    form_repeat = []
    app.show_form()
    form = app._content
    form._length.set("16")
    for var in form._sets.values():
        var.set(True)
    for _ in range(3):
        form._generate()
        form_repeat.append(form._vars["password"].get())
    ok = len(set(form_repeat)) == 3 and all(len(p) == 16 for p in form_repeat)
    rec("P-10 повторное нажатие «Сгенерировать»", "Passed" if ok else "Failed", f"уникальных паролей: {len(set(form_repeat))} из 3")


def t_double_save():
    app.show_form()
    form = app._content
    before = len(app.repo.list_all())
    form._vars["service"].set("DoubleClick")
    form._vars["password"].set("Dbl-1!")
    save_button = [w for w in form.winfo_children() if isinstance(w, tkinter.Widget) and w.winfo_class() == "TFrame"]
    form._save()
    after_first = len(app.repo.list_all())
    try:
        form._save()
    except Exception:
        pass
    after_second = len(app.repo.list_all())
    rec("P-11 повторное «Сохранить» не создаёт дубль", "Passed" if after_second == after_first == before + 1 else "Failed",
        f"до {before}, после 1-го {after_first}, после 2-го {after_second}",
        note="после первого сохранения форма закрыта; повторный вызов на уничтоженной форме")
    settle(app)


def t_delete_cancel_and_confirm():
    lst = app._content
    lst._query.set("")
    n = len(app.repo.list_all())
    item = lst._tree.get_children()[0]
    lst._tree.selection_set(item)
    ANSWER["yes"] = False
    lst._delete()
    kept = len(app.repo.list_all()) == n
    ANSWER["yes"] = True
    lst._delete()
    deleted = len(app.repo.list_all()) == n - 1
    rec("P-12 удаление: отказ сохраняет, подтверждение удаляет", "Passed" if kept and deleted else "Failed",
        f"отказ={kept}, подтверждение={deleted}")


def t_search_big():
    app.show_form()
    for i in range(300):
        app.repo.add(Entry(service=f"Svc{i}", login=f"user{i}", password=f"P{i}-x!"))
    app.show_list()
    settle(app)
    started = time.perf_counter()
    app._content._query.set("svc2")
    elapsed = time.perf_counter() - started
    found = len(app._content._tree.get_children())
    rec("P-13 поиск по 300+ записям в UI", "Passed" if elapsed < 0.5 else "Failed",
        f"{elapsed:.3f} с, найдено {found}")


def t_search_special():
    lst = app._content
    lst._query.set("'; DROP TABLE entries;--")
    rec("P-14 спецсимволы в поиске", "Passed" if len(lst._tree.get_children()) == 0 else "Failed",
        "пустой результат, таблица на месте" if app.repo.list_all() else "")
    lst._query.set("")
    settle(app)


def t_copy_and_lock():
    lst = app._content
    item = lst._tree.get_children()[0]
    lst._tree.selection_set(item)
    lst._copy()
    got = app.clipboard_get()
    app.lock()
    settle(app)
    try:
        clip = app.clipboard_get()
    except tkinter.TclError:
        clip = ""
    rec("P-15 копирование и очистка при «Выйти»", "Passed" if got and clip == "" else "Failed",
        f"в буфере до выхода: {bool(got)}, после выхода: {'пусто' if clip == '' else clip}")


def t_unlock_wrong_and_empty():
    login = app._content
    fill(login._master, "")
    login._submit()
    e1 = login._error.cget("text")
    fill(login._master, "wrong-pass")
    login._submit()
    e2 = login._error.cget("text")
    rec("P-16 вход: пустой и неверный пароль", "Passed" if e1 == "Введите мастер-пароль." and e2 == "Неверный мастер-пароль." else "Failed",
        f"'{e1}' / '{e2}'")


def t_unlock_ok_and_data_kept():
    login = app._content
    fill(login._master, "Master-1!")
    login._submit()
    settle(app)
    rec("P-17 вход верным паролем, данные на месте", "Passed" if len(app.repo.list_all()) > 0 else "Failed",
        f"записей: {len(app.repo.list_all())}")


def t_close_with_timer():
    app.show_list()
    lst = app._content
    if lst._tree.get_children():
        lst._tree.selection_set(lst._tree.get_children()[0])
        lst._copy()
    try:
        app.close()
        rec("P-18 закрытие окна с активным таймером буфера", "Passed", "закрыто без исключений")
    except Exception as exc:
        rec("P-18 закрытие окна с активным таймером буфера", "Failed", f"{type(exc).__name__}: {exc}")


steps = [t_empty_create, t_create, t_empty_service_and_password, t_long_service, t_long_password_roundtrip,
         t_unicode_password, t_length_input, t_strength_levels, t_generator_repeat, t_double_save,
         t_delete_cancel_and_confirm, t_search_big, t_search_special, t_copy_and_lock,
         t_unlock_wrong_and_empty, t_unlock_ok_and_data_kept, t_close_with_timer]
SKIP = set(os.environ.get("SKIP", "").split(",")) - {""}
SKIP = set(os.environ.get("SKIP", "").split(",")) - {""}
for step in steps:
    if step.__name__ in SKIP:
        print("SKIP", step.__name__, flush=True)
        continue
    safe(step.__name__, step)

for r in RESULTS:
    print(f"{r['status']:7} {r['case']} | {r['actual']} | {r['note']}")
print("всплывающие окна:", SHOWN)
print("ИТОГО: passed", sum(r["status"] == "Passed" for r in RESULTS), "failed", sum(r["status"] == "Failed" for r in RESULTS))
