import sqlite3

def delete_user_by_email(email):
    conn = sqlite3.connect('trader_diary.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    print(f"Пользователь с email '{email}' удалён.")

    conn.close()

if __name__ == "__main__":
    email_to_delete = input("Введите email пользователя для удаления: ").strip()
    delete_user_by_email(email_to_delete)
