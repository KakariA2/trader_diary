import sqlite3

conn = sqlite3.connect('trades.db')
cur = conn.cursor()

cur.execute("PRAGMA table_info(journal)")
columns = [info[1] for info in cur.fetchall()]

if 'screenshot' not in columns:
    cur.execute("ALTER TABLE journal ADD COLUMN screenshot TEXT")
    print("Колонка 'screenshot' добавлена в таблицу journal")
else:
    print("Колонка 'screenshot' уже существует")

conn.commit()
conn.close()
