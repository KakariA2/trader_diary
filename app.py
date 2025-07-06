from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import logging
import secrets
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, session, url_for
)
from werkzeug.security import generate_password_hash
from flask_dance.contrib.google import make_google_blueprint, google

# ───── Flask-приложение ─────
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey_fallback')

# ───── Разрешаем работу без HTTPS для локальной отладки ─────
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# ───── Google OAuth Blueprint ─────
google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    scope=["profile", "email"],
    redirect_url="/google/authorized"
)
app.register_blueprint(google_bp, url_prefix="/google")

# ───── База данных ─────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'trades.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            subscription_status TEXT DEFAULT 'free',
            trial_start_date TEXT,
            premium_end_date TEXT,
            is_verified INTEGER DEFAULT 1,
            verification_token TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pair TEXT NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            lot REAL NOT NULL,
            profit REAL NOT NULL,
            comment TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        conn.commit()

# ───── Главная страница ─────
@app.route("/")
def index():
    now = datetime.now()
    current_year = now.year
    selected_year = int(request.args.get('year', current_year))
    selected_month = int(request.args.get('month', now.month))

    years = list(range(2020, current_year + 6))
    months = [(i, name) for i, name in enumerate(
        ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
         'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'], 1)]

    demo_trades = [{
        'pair': 'EUR/USD', 'date': '2025-07-04 12:00',
        'type': 'Buy', 'lot': 0.1, 'profit': 10.0,
        'comment': 'Удачная сделка'
    }]

    return render_template(
        'index.html',
        session=session,
        premium_end_date=None,
        texts={
            'total_profit': 'Общая прибыль/убыток',
            'profit_by_pair': 'Прибыль по валютным парам'
        },
        total_profit=123.45,
        profit_by_pair={'EUR/USD': 50, 'GBP/USD': -20},
        years=years, months=months,
        selected_year=selected_year,
        selected_month=selected_month,
        trades=demo_trades
    )

# ───── Google OAuth Callback ─────
@app.route("/google/authorized")
def google_authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Ошибка получения данных от Google", 500

    info = resp.json()
    email = info["email"]
    username = info.get("name", email.split("@")[0])

    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None:
            pw_hash = generate_password_hash(secrets.token_urlsafe(16))
            premium_end = (datetime.utcnow() + timedelta(days=7)).isoformat()
            conn.execute(
                "INSERT INTO users (username, email, password_hash, premium_end_date) VALUES (?, ?, ?, ?)",
                (username, email, pw_hash, premium_end)
            )
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    session['user_id'] = user['id']
    session['username'] = user['username']
    return redirect("/")

# ───── Выход ─────
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ───── Запуск ─────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
