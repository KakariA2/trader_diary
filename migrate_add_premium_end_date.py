import sqlite3

def migrate_add_premium_end_date():
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()

    # Проверяем, есть ли колонка premium_end_date
    cursor.execute("PRAGMA table_info(users);")
    columns = [info[1] for info in cursor.fetchall()]
    if 'premium_end_date' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN premium_end_date TEXT;")
        print("Колонка premium_end_date добавлена.")
    else:
        print("Колонка premium_end_date уже существует.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_add_premium_end_date()
