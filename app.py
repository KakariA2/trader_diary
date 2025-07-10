from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import logging
from datetime import datetime

from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from flask_dance.contrib.google import make_google_blueprint
from flask import session, render_template, request
from datetime import datetime
from flask import redirect, url_for
from flask_dance.contrib.google import google

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey_fallback')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
JOURNAL_SCREEN_FOLDER = os.path.join('static', 'journal_screens')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JOURNAL_SCREEN_FOLDER'] = JOURNAL_SCREEN_FOLDER

# Создаем папки, если их нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['JOURNAL_SCREEN_FOLDER'], exist_ok=True)

# Google OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    # убираем redirect_url полностью!
    # redirect_url="/google/authorized"  <- убираем эту строку
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
        cur.execute('''CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT,
            thoughts TEXT,
            emotion TEXT,
            errors TEXT,
            goal TEXT,
            screenshot TEXT,
            goal_achieved INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            premium_end_date TEXT
        )''')
        conn.commit()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Получаем сделки, прибыль и пр.
    with get_db_connection() as conn:
        # Итоговая прибыль
        total_profit = conn.execute('SELECT SUM(profit) FROM trades WHERE user_id = ?', (user_id,)).fetchone()[0]
        total_profit = total_profit if total_profit is not None else 0.0

        # Прибыль по инструментам
        rows = conn.execute('''
            SELECT pair, SUM(profit) as pair_profit
            FROM trades
            WHERE user_id = ?
            GROUP BY pair
        ''', (user_id,)).fetchall()
        profit_by_pair = {row['pair']: row['pair_profit'] for row in rows}

        # Получаем все сделки пользователя (например, за последний месяц или все)
        trades = conn.execute('''
            SELECT * FROM trades WHERE user_id = ? ORDER BY date DESC LIMIT 50
        ''', (user_id,)).fetchall()

        # Получаем дату окончания премиум-подписки пользователя (если есть)
        premium_end_date = conn.execute('SELECT premium_end_date FROM users WHERE id = ?', (user_id,)).fetchone()
        premium_end_date = premium_end_date[0] if premium_end_date and premium_end_date[0] else None

    # Для фильтра по датам
    now = datetime.now()
    years = list(range(2022, now.year + 1))
    months = [(i, name) for i, name in enumerate(
        ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
         'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'], 1)]

    # По умолчанию текущий год и месяц
    selected_year = request.args.get('year', now.year, type=int)
    selected_month = request.args.get('month', now.month, type=int)

    texts = {
        'total_profit': 'Итоговая прибыль',
        'profit_by_pair': 'Прибыль по инструментам',
    }

    return render_template(
        'index.html',
        texts=texts,
        total_profit=total_profit,
        profit_by_pair=profit_by_pair,
        trades=trades,
        premium_end_date=premium_end_date,
        years=years,
        months=months,
        selected_year=selected_year,
        selected_month=selected_month
    )

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
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_") + secure_filename(screenshot.filename)
            screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            screenshot.save(screenshot_path)
            screenshot_filename = filename

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

@app.route("/journal", methods=["GET", "POST"])
def journal():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session["user_id"]

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    selected_year = int(request.args.get('year', current_year))
    selected_month = int(request.args.get('month', current_month))
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    if request.method == "POST":
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        thoughts = request.form.get("thoughts")
        emotion = request.form.get("emotion")
        errors = request.form.get("errors")
        goal = request.form.get("goal")
        screenshot = request.files.get("screenshot")

        screenshot_filename = None
        if screenshot and screenshot.filename:
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_") + secure_filename(screenshot.filename)
            path = os.path.join(app.config['JOURNAL_SCREEN_FOLDER'], filename)
            os.makedirs(app.config['JOURNAL_SCREEN_FOLDER'], exist_ok=True)
            screenshot.save(path)
            screenshot_filename = filename

        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO journal (user_id, date, thoughts, emotion, errors, goal, screenshot, goal_achieved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, date, thoughts, emotion, errors, goal, screenshot_filename, 0))
            conn.commit()
        return redirect("/journal")

    with get_db_connection() as conn:
        entries = conn.execute('''
            SELECT * FROM journal
            WHERE user_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        ''', (user_id, str(selected_year), f"{selected_month:02}", per_page, offset)).fetchall()

        total_entries = conn.execute('''
            SELECT COUNT(*) FROM journal
            WHERE user_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ''', (user_id, str(selected_year), f"{selected_month:02}")).fetchone()[0]

    total_pages = (total_entries + per_page - 1) // per_page

    years = list(range(2022, current_year + 1))
    months = [(i, name) for i, name in enumerate(
        ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
         'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'], 1)]

    achieved_goals = sum(1 for entry in entries if entry["goal_achieved"])
    total_goals = len(entries)

    return render_template("journal.html",
        entries=entries,
        years=years,
        months=months,
        selected_year=selected_year,
        selected_month=selected_month,
        current_page=page,
        total_pages=total_pages,
        achieved=achieved_goals,
        total=total_goals
    )

@app.route('/update_goal/<int:entry_id>', methods=['POST'])
def update_goal(entry_id):
    if 'user_id' not in session:
        return redirect('/')

    achieved = 1 if request.form.get('goal_achieved') == 'on' else 0

    with get_db_connection() as conn:
        conn.execute('''
            UPDATE journal SET goal_achieved = ? WHERE id = ? AND user_id = ?
        ''', (achieved, entry_id, session['user_id']))
        conn.commit()

    return redirect('/journal')

def migrate_db():
    with get_db_connection() as conn:
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(trades)")
        trades_columns = [info[1] for info in cur.fetchall()]
        if 'screenshot' not in trades_columns:
            print("Миграция: добавляем колонку screenshot в trades")
            cur.execute("ALTER TABLE trades ADD COLUMN screenshot TEXT")
            conn.commit()

        cur.execute("PRAGMA table_info(journal)")
        journal_columns = [info[1] for info in cur.fetchall()]
        required = ['thoughts', 'emotion', 'errors', 'goal', 'screenshot', 'goal_achieved']
        for col in required:
            if col not in journal_columns:
                print(f"Миграция: добавляем колонку {col} в journal")
                if col == 'goal_achieved':
                    cur.execute(f"ALTER TABLE journal ADD COLUMN {col} INTEGER DEFAULT 0")
                else:
                    cur.execute(f"ALTER TABLE journal ADD COLUMN {col} TEXT")
                conn.commit()

def get_or_create_user(user_info):
    email = user_info.get("email")
    username = user_info.get("name", email.split('@')[0])

    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None:
            cur = conn.cursor()
            # В поле password_hash можно записать пустую строку или NULL, если пользователь через Google
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, ""))
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return user["id"]

@app.route('/login')
def login():
    if not google.authorized:
        return redirect(url_for("google.login"))  # Перенаправляем на Google OAuth
    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        user_info = resp.json()
        # Тут должна быть логика: сохраняем user_info в сессию, создаём пользователя в БД и т.д.
        # Например:
        session['user_id'] = get_or_create_user(user_info)
        return redirect('/')
    else:
        return "Не удалось получить информацию о пользователе"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    init_db()
    migrate_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
