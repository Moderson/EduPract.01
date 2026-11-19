# Диаграммы последовательности (день 3)

## Сценарий 1. Первый запуск: создание мастер-пароля (US-1, M1)
```mermaid
sequenceDiagram
    actor U as Пользователь
    participant UI
    participant C as core.crypto
    participant D as Данные
    U->>UI: ввод мастер-пароля
    UI->>C: derive_key(master, salt)
    C-->>UI: key
    UI->>C: make_verifier(key)
    C-->>UI: verifier
    UI->>D: сохранить salt и verifier
    D-->>UI: готово
```

## Сценарий 2. Добавление записи с генерацией пароля (US-2, US-5, M2)
```mermaid
sequenceDiagram
    actor U as Пользователь
    participant UI
    participant G as core.generator
    participant S as core.strength
    participant C as core.crypto
    participant D as Данные
    U->>UI: нажать Сгенерировать
    UI->>G: generate_password(length, наборы)
    G-->>UI: пароль
    UI->>S: password_strength(пароль)
    S-->>UI: weak, medium или strong
    U->>UI: сохранить запись
    UI->>C: encrypt_password(пароль, key)
    C-->>UI: токен
    UI->>D: сохранить Entry с токеном
```

## Сценарий 3. Поиск и показ пароля (US-6, US-7, M6, M7)
```mermaid
sequenceDiagram
    actor U as Пользователь
    participant UI
    participant F as core.search
    participant M as core.masking
    participant C as core.crypto
    U->>UI: ввод строки поиска
    UI->>F: filter_entries(записи, строка)
    F-->>UI: отфильтрованный список
    UI->>M: mask_password(пароль)
    M-->>UI: MASK
    U->>UI: нажать Показать
    UI->>C: decrypt_password(токен, key)
    C-->>UI: пароль
    UI->>M: unmask_password(пароль)
    M-->>UI: пароль в открытом виде
```
