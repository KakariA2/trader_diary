import sqlite3
import os

# Список баз данных для проверки
databases = ['trades.db', 'trader_diary.db']

for db_file in databases:
    if os.path.exists(db_file):
        print(f"\n📂 База данных: {db_file}")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            if tables:
                print("   🧾 Таблицы:")
                for table in tables:
                    print(f"     - {table[0]}")
            else:
                print("   ⚠️ Нет таблиц в этой базе.")
            conn.close()
        except Exception as e:
            print(f"   ❌ Ошибка при чтении базы: {e}")
    else:
        print(f"\n🚫 Файл базы данных не найден: {db_file}")
