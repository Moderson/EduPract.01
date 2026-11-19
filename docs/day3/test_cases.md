# Тест-кейсы ядра (день 3)

Метод: чёрный ящик, функциональное тестирование и граничные значения. Колонки «Факт» и «Статус» заполняются после слияния ветки разработчика.

| ID | Требование | Предусловие | Шаги | Ожидаемый результат | Факт | Статус |
|---|---|---|---|---|---|---|
| TC-01 | M5 | ядро импортируется | generate_password(8) | строка длины 8 | | |
| TC-02 | M5 | | generate_password(64) | строка длины 64 | | |
| TC-03 | M5 | | generate_password(7) | ValueError | | |
| TC-04 | M5 | | generate_password(65) | ValueError | | |
| TC-05 | M5 | | generate_password(12, False, False, False, False) | ValueError «Выберите хотя бы один набор символов» | | |
| TC-06 | M5, US-5 | | generate_password(20, False, False, True, False) | только цифры | | |
| TC-07 | M5, US-5 | | generate_password(8, True, True, True, True) 50 раз | в каждом пароле есть символ каждого набора | | |
| TC-08 | S2 | | password_strength("abc") | weak | | |
| TC-09 | S2 | | password_strength("Password1") | medium | | |
| TC-10 | S2 | | password_strength("Xk9#mQ2$vLp7!zRt") | strong | | |
| TC-11 | S2 | | password_strength("") | weak, без исключения | | |
| TC-12 | M6, US-6 | | mask_password("a") и mask_password("очень длинный пароль") | оба раза 8 точек | | |
| TC-13 | M6 | | mask_password("") | пустая строка | | |
| TC-14 | M7, US-7 | записи GitHub/alice и Mail/Bob | filter_entries(записи, "github") | одна запись GitHub | | |
| TC-15 | M7 | те же записи | filter_entries(записи, "BOB") | запись Mail (поиск по логину без учёта регистра) | | |
| TC-16 | M7 | те же записи | filter_entries(записи, "") | обе записи | | |
| TC-17 | M7 | те же записи | filter_entries(записи, "zzz") | пустой список | | |
| TC-18 | M1, US-1 | salt и verifier созданы для «master» | verify_master("master", ...) и verify_master("wrong", ...) | True и False | | |
| TC-19 | M4, US-4 | ключ получен | encrypt_password("s3cret!", key) | токен не содержит s3cret, decrypt возвращает исходную строку | | |
| TC-20 | M4 | токен зашифрован ключом A | decrypt_password(токен, ключ B) | InvalidToken | | |
| TC-21 | NFR | | вызов всех функций | пароли не печатаются в консоль и не пишутся в лог | | |
