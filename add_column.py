import sqlite3

def add_column_thoughts():
    conn = sqlite3.connect('trades.db')
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(journal)")
    columns = [info[1] for info in cur.fetchall()]

    if 'thoughts' not in columns:
        cur.execute("ALTER TABLE journal ADD COLUMN thoughts TEXT")
        print("Колонка 'thoughts' добавлена в таблицу journal")
    else:
        print("Колонка 'thoughts' уже есть")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_column_thoughts()
