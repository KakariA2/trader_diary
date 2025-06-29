import sqlite3

def print_db_structure(db_path='trades.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Таблицы в базе:", [t[0] for t in tables])

    for table_name in tables:
        name = table_name[0]
        print(f"\nСтруктура таблицы '{name}':")
        cursor.execute(f"PRAGMA table_info({name})")
        columns = cursor.fetchall()
        for col in columns:
            # Выводим: cid, имя колонки, тип, notnull, default_value, pk
            print(f"  {col}")

    conn.close()

if __name__ == '__main__':
    print_db_structure()
