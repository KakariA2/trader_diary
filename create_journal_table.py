import sqlite3

def create_journal_table():
    conn = sqlite3.connect('trades.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            thoughts TEXT,
            emotion TEXT,
            errors TEXT,
            goal TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    print("Таблица journal создана или уже существует")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_journal_table()
