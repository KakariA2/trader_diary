from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Замените на свой секретный ключ

# Абсолютный путь к файлу базы данных рядом с app.py
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'trades.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Чтобы обращаться к колонкам по имени
    return conn


# Создаём таблицы, если их нет (инициализация базы)
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
        is_verified INTEGER NOT NULL DEFAULT 0,
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


# Главная страница с отображением сделок и информации о подписке
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    user = conn.execute(
        'SELECT * FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    trades = conn.execute(
        'SELECT * FROM trades WHERE user_id = ? ORDER BY date DESC',
        (session['user_id'],)
    ).fetchall()

    total_profit = conn.execute(
        'SELECT SUM(profit) FROM trades WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()[0] or 0

    profit_rows = conn.execute(
        'SELECT pair, SUM(profit) FROM trades WHERE user_id = ? GROUP BY pair',
        (session['user_id'],)
    ).fetchall()
    profit_by_pair = {row['pair']: row['SUM(profit)'] for row in profit_rows}

    years_rows = conn.execute(
        "SELECT DISTINCT strftime('%Y', date) AS year FROM trades WHERE user_id = ? ORDER BY year DESC",
        (session['user_id'],)
    ).fetchall()
    years = [int(row['year']) for row in years_rows if row['year']]

    months = [
        (1, 'Январь'), (2, 'Февраль'), (3, 'Март'), (4, 'Апрель'),
        (5, 'Май'), (6, 'Июнь'), (7, 'Июль'), (8, 'Август'),
        (9, 'Сентябрь'), (10, 'Октябрь'), (11, 'Ноябрь'), (12, 'Декабрь')
    ]

    selected_year = years[0] if years else datetime.now().year
    selected_month = datetime.now().month

    conn.close()

    return render_template('index.html',
                           trades=trades,
                           total_profit=total_profit,
                           profit_by_pair=profit_by_pair,
                           texts={
                               'total_profit': 'Общая прибыль/Убыток',
                               'profit_by_pair': 'Прибыль по валютным парам'
                           },
                           years=years,
                           months=months,
                           selected_year=selected_year,
                           selected_month=selected_month,
                           premium_end_date=user['premium_end_date'] if user and user['premium_end_date'] else None
                           )


# Регистрация пользователя с установкой даты окончания подписки (7 дней)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if not username or not email or not password:
            return 'Заполните все поля'

        hashed_password = generate_password_hash(password)

        now = datetime.utcnow()
        premium_end = now + timedelta(days=7)
        premium_end_str = premium_end.isoformat()

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password_hash, premium_end_date) VALUES (?, ?, ?, ?)',
                (username, email, hashed_password, premium_end_str)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return 'Пользователь с таким именем или почтой уже существует'
        conn.close()

        return redirect('/login')
    return render_template('register.html')


# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?',
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/')
        else:
            return 'Неверный логин или пароль'

    return render_template('login.html')


# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# Добавление новой сделки
@app.route('/add_trade', methods=['POST'])
def add_trade():
    if 'user_id' not in session:
        return redirect('/login')

    pair = request.form['pair'].strip()
    date = request.form['date']
    type_ = request.form['type']
    lot = request.form['lot']
    profit = request.form['profit']
    comment = request.form.get('comment', '').strip()

    if not pair or not date or not type_ or not lot or not profit:
        return 'Заполните все обязательные поля сделки'

    try:
        lot = float(lot)
        profit = float(profit)
    except ValueError:
        return 'Лот и прибыль должны быть числами'

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO trades (user_id, pair, date, type, lot, profit, comment) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (session['user_id'], pair, date, type_, lot, profit, comment)
    )
    conn.commit()
    conn.close()

    return redirect('/')


if __name__ == '__main__':
    init_db()  # Создаем таблицы при старте, если их нет
    app.run(host='0.0.0.0', port=5000, debug=True)
