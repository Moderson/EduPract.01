# Ручная проверка ядра (день 3)

Заполняется тестировщиком после слияния ветки разработчика в feature.

- Дата проверки:
- Ветка и коммит:
- Python:
- Проверяющий: Шипунов Е. А.

## Подготовка
```
pip install -r requirements.txt
python -c "from src.core.generator import generate_password as g; print(len(g()))"
```
Если команда падает с ImportError, проверь наличие src/__init__.py и src/core/__init__.py и запускай из корня репозитория.

## Сценарии
| № | Сценарий | Как проверить | Результат (ОК / баг) | Комментарий |
|---|---|---|---|---|
| 1 | Генерация пароля по умолчанию | `python -c "from src.core.generator import generate_password as g; p=g(); print(len(p))"` | | |
| 2 | Граница длины | то же с g(7) и g(65), ожидается ValueError | | |
| 3 | Все наборы выключены | g(12, False, False, False, False) | | |
| 4 | Проверка мастер-пароля | derive_key, make_verifier, verify_master с верным и неверным паролем | | |
| 5 | Шифрование и расшифровка | encrypt_password, decrypt_password, сравнить с исходной строкой | | |
| 6 | Поиск без учёта регистра | filter_entries на трёх записях | | |
| 7 | Маскирование | mask_password для паролей разной длины | | |
| 8 | Автотесты | `python -m pytest tests` | | |

## Итог
Все сценарии пройдены: да / нет
Найденные дефекты: см. docs/day3/bugs.md
