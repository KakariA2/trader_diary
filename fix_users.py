import sqlite3

# Подключаемся к базе
conn = sqlite3.connect("trader_diary.db")
cursor = conn.cursor()

# Добавляем недостающие поля, если их нет
try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
    print("✅ Поле 'is_verified' добавлено.")
except sqlite3.OperationalError as e:
    print("⚠️ Поле 'is_verified' уже существует.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
    print("✅ Поле 'verification_token' добавлено.")
except sqlite3.OperationalError as e:
    print("⚠️ Поле 'verification_token' уже существует.")

conn.commit()
conn.close()
print("🎉 Готово.")
