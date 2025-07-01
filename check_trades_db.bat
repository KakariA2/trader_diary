@echo off
echo Открываем базу данных trades.db и проверяем структуру...

sqlite3 trades.db ".tables"
echo.

echo ==== Структура таблицы users ====
sqlite3 trades.db ".schema users"
echo.

echo ==== Структура таблицы trades ====
sqlite3 trades.db ".schema trades"
echo.

pause
