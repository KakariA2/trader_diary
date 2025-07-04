from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные окружения из .env

import os
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import logging

print("SECRET_KEY =", os.getenv('SECRET_KEY'))
print("GOOGLE_CLIENT_ID =", os.getenv('GOOGLE_CLIENT_ID'))
print("GOOGLE_CLIENT_SECRET =", os.getenv('GOOGLE_CLIENT_SECRET'))

# Для Google OAuth
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')  # Лучше всегда задавать в .env

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'trades.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        subscription_status TEXT NOT NULL DEFAULT 'free',
        trial_start_date TEXT,
        premium_end_date TEXT,
        is_verified INTEGER NOT NULL DEFAULT 1,
        verification_token TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pair TEXT NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        lot REAL NOT NULL,
        profit REAL NOT NULL,
        comment TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"],
    redirect_url="/google_login/callback"
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/google_login/callback")
def google_login_callback():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Ошибка при получении информации с Google", 500

    user_info = resp.json()
    email = user_info["email"]
    username = user_info.get("name", email.split("@")[0])

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if user is None:
        hashed_password = generate_password_hash(secrets.token_urlsafe(16))  # случайный пароль
        now = datetime.utcnow()
        premium_end = now + timedelta(days=7)
        premium_end_str = premium_end.isoformat()
        conn.execute(
            "INSERT INTO users (username, email, password_hash, premium_end_date, is_verified) VALUES (?, ?, ?, ?, ?)",
            (username, email, hashed_password, premium_end_str, 1)
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    session['user_id'] = user['id']
    session['username'] = user['username']

    return redirect("/")

# --- остальные маршруты и функции ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
