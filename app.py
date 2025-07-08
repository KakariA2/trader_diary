from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import logging
import secrets
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey_fallback')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/add_trade', methods=['GET', 'POST'])
def add_trade():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        user_id = session['user_id']
        pair = request.form.get('pair')
        date = request.form.get('date')
        trade_type = request.form.get('type')
        lot = request.form.get('lot')
        profit = request.form.get('profit')
        comment = request.form.get('comment')
        screenshot = request.files.get('screenshot')

        screenshot_filename = None
        if screenshot and screenshot.filename:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_") + secure_filename(screenshot.filename)
            screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            screenshot.save(screenshot_path)
            screenshot_filename = filename  # сохраняем только имя файла
        else:
            screenshot_filename = None  # если файла нет, то None

        try:
            lot = float(lot)
            profit = float(profit)
        except (TypeError, ValueError):
            return redirect('/')

        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO trades (user_id, pair, date, type, lot, profit, comment, screenshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, pair, date, trade_type, lot, profit, comment, screenshot_filename))
            conn.commit()

        return redirect('/')

    return render_template('add_trade.html')

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_url="/google/authorized"
)
app.register_blueprint(google_bp, url_prefix="/google")

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
            screenshot TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        # Новая таблица promo_codes
        cur.execute('''CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            free_days INTEGER DEFAULT 0,
            discount_percent INTEGER DEFAULT NULL,
            active INTEGER DEFAULT 1
        )''')

        conn.commit()

from datetime import datetime

def migrate_db():
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Проверяем, есть ли столбец 'screenshot' в таблице trades
        cur.execute("PRAGMA table_info(trades)")
        columns = [info[1] for info in cur.fetchall()]
        if 'screenshot' not in columns:
            print("Миграция: добавляем колонку screenshot в trades")
            cur.execute("ALTER TABLE trades ADD COLUMN screenshot TEXT")
            conn.commit()
from flask import flash

@app.route('/promo_code', methods=['GET', 'POST'])
def promo_code():
    if 'user_id' not in session:
        return redirect('/')

    message = None
    success = False

    if request.method == 'POST':
        code_input = request.form.get('promo_code', '').strip()

        with get_db_connection() as conn:
            promo = conn.execute('''
                SELECT * FROM promo_codes
                WHERE code = ? AND active = 1
                  AND date('now') BETWEEN start_date AND end_date
            ''', (code_input,)).fetchone()

            if promo:
                # Допустим, обновим пользователя — добавим free_days к premium_end_date
                user_id = session['user_id']
                user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

                now = datetime.utcnow()

                premium_end = user['premium_end_date']
                if premium_end:
                    premium_end_dt = datetime.fromisoformat(premium_end)
                    if premium_end_dt < now:
                        premium_end_dt = now
                else:
                    premium_end_dt = now

                # Добавляем free_days из промокода
                premium_end_dt += timedelta(days=promo['free_days'])

                conn.execute('''
                    UPDATE users SET premium_end_date = ?
                    WHERE id = ?
                ''', (premium_end_dt.isoformat(), user_id))
                conn.commit()

                message = f"Промокод '{code_input}' активирован! Ваш премиум продлён на {promo['free_days']} дней."
                success = True
            else:
                message = "Промокод недействителен или истёк."

    return render_template('promo_code.html', message=message, success=success)

@app.route('/add_test_promo')
def add_test_promo():
    with get_db_connection() as conn:
        conn.execute('''
            INSERT OR IGNORE INTO promo_codes
            (code, description, start_date, end_date, free_days, discount_percent, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('TESTPROMO', 'Тестовый промокод', '2025-01-01', '2025-12-31', 5, None, 1))
        conn.commit()
    return "Тестовый промокод добавлен: TESTPROMO"

@app.route("/")
def index():
    if 'user_id' not in session:
        return render_template("welcome.html")

    user_id = session['user_id']
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    selected_year = int(request.args.get('year', current_year))
    selected_month = int(request.args.get('month', current_month))

    years = list(range(2020, current_year + 6))
    months = [(i, name) for i, name in enumerate(
        ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
         'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'], 1)]

    with get_db_connection() as conn:
       trades = conn.execute(
    """
    SELECT * FROM trades 
    WHERE user_id = ?
    AND date LIKE ?
    ORDER BY date DESC
    """,
    (user_id, f"{selected_year}-{selected_month:02}%")
).fetchall()

    total_profit = sum([trade['profit'] for trade in trades]) if trades else 0

    profit_by_pair = {}
    for trade in trades:
        pair = trade['pair']
        profit_by_pair[pair] = profit_by_pair.get(pair, 0) + trade['profit']

    return render_template(
        'index.html',
        session=session,
        premium_end_date=None,
        texts={
            'total_profit': 'Общая прибыль/убыток',
            'profit_by_pair': 'Прибыль по валютным парам'
        },
        total_profit=total_profit,
        profit_by_pair=profit_by_pair,
        years=years,
        months=months,
        selected_year=selected_year,
        selected_month=selected_month,
        trades=trades
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if not username or not email or not password:
            return render_template("register.html", error="Все поля обязательны.")
        
        if password != confirm:
            return render_template("register.html", error="Пароли не совпадают.")
        
        password_hash = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash)
                )
                conn.commit()
            return redirect('/')
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Такой логин или email уже зарегистрирован.")
    
    return render_template("register.html")

@app.route('/check_user', methods=['POST'])
def check_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT 1 FROM users WHERE username = ? OR email = ? LIMIT 1",
            (username, email)
        ).fetchone()

    return jsonify({'exists': bool(user)})

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

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
    return redirect('/')

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        topic = request.form.get("topic")
        message = request.form.get("message")
        timestamp = datetime.utcnow().isoformat()

        if not name or not email or not message:
            return "Пожалуйста, заполните все обязательные поля", 400

        with get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    topic TEXT,
                    message TEXT,
                    timestamp TEXT
                )
            ''')
            conn.execute('''
                INSERT INTO feedback (name, email, topic, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, topic, message, timestamp))
            conn.commit()

        return render_template("feedback.html", success=True)

    return render_template("feedback.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    init_db()
    migrate_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
