import sqlite3

conn = sqlite3.connect('trader_diary.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair TEXT NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    lot REAL NOT NULL,
    profit REAL NOT NULL,
    comment TEXT
)
''')

conn.commit()
conn.close()

print("Таблица trades успешно создана (если её не было).")
