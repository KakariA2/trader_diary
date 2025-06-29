import sqlite3

conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Таблица пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
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

# Таблица сделок
cursor.execute('''
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pair TEXT NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    lot REAL NOT NULL,
    profit REAL NOT NULL,
    comment TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()

print("Таблицы users и trades успешно созданы (если их не было)")
