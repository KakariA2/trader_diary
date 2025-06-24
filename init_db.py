import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Создаём таблицу users
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    subscription_status TEXT NOT NULL DEFAULT 'free',
    trial_start_date TEXT,
    premium_end_date TEXT
)
''')

conn.commit()
conn.close()

print("Таблица users успешно создана.")
