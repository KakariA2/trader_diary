import sqlite3

conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

# Задай здесь user_id, на который хочешь обновить старые сделки
target_user_id = 1  # Например, 1 — первый пользователь

# Обновляем все записи с user_id=0 на target_user_id
cursor.execute('''
UPDATE trades
SET user_id = ?
WHERE user_id = 0
''', (target_user_id,))

conn.commit()
conn.close()

print(f"Обновлены все сделки с user_id=0 на user_id={target_user_id}")
