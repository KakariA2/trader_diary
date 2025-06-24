import sqlite3

conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Создаем новую таблицу с дополнительными полями
cursor.execute('''
CREATE TABLE IF NOT EXISTS users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    subscription_status TEXT NOT NULL DEFAULT 'free',
    trial_start_date TEXT,
    premium_end_date TEXT,
    is_verified INTEGER NOT NULL DEFAULT 0,
    verification_token TEXT
)
''')

# Копируем данные из старой таблицы в новую
cursor.execute('''
INSERT INTO users_new (id, username, email, password_hash, subscription_status, trial_start_date, premium_end_date, is_verified, verification_token)
SELECT id, username, email, password_hash, subscription_status, trial_start_date, premium_end_date, 0, NULL FROM users
''')

# Удаляем старую таблицу
cursor.execute('DROP TABLE users')

# Переименовываем новую таблицу
cursor.execute('ALTER TABLE users_new RENAME TO users')

conn.commit()
conn.close()

print("Таблица users обновлена с новыми полями для подтверждения email.")
