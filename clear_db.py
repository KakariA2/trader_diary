import sqlite3

conn = sqlite3.connect('trader_diary.db')
cursor = conn.cursor()

# Очистка всех таблиц
cursor.execute("DELETE FROM users")
cursor.execute("DELETE FROM trades")
cursor.execute("DELETE FROM feedback")

conn.commit()
conn.close()

print("✅ База данных очищена.")
