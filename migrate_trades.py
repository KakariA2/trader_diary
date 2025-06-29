import sqlite3

conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Создаем новую таблицу trades_new с user_id
cursor.execute('''
CREATE TABLE IF NOT EXISTS trades_new (
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

# Копируем данные из старой trades в trades_new, user_id ставим 0 (нужно потом исправить)
cursor.execute('''
INSERT INTO trades_new (id, user_id, pair, date, type, lot, profit, comment)
SELECT id, 0, pair, date, type, lot, profit, comment FROM trades
''')

# Удаляем старую таблицу
cursor.execute('DROP TABLE trades')

# Переименовываем trades_new в trades
cursor.execute('ALTER TABLE trades_new RENAME TO trades')

conn.commit()
conn.close()

print("Миграция trades завершена: добавлено поле user_id, данные перенесены с user_id=0.")
