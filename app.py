from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
import shutil
import datetime
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'trader_diary_secret_key'

# Переводы
translations = {
    'ru': {
        'title': 'Дневник трейдера',
        'total_profit': 'Общая прибыль/убыток',
        'profit_by_pair': 'Прибыль по валютным парам',
        'pair': 'Пара',
        'date': 'Дата',
        'type': 'Тип',
        'lot': 'Лот',
        'profit_loss': 'Прибыль/Убыток',
        'comment': 'Комментарий',
        'buy': 'Buy',
        'sell': 'Sell',
        'save': '💾 Сохранить',
        'support': 'Угости кофе за удачную сделку',
        'buymeacoffee': 'Buymeacoffee',
        'paypal': 'PayPal',
        'boosty': 'Boosty',
    }
}

# Email при ошибках

def send_error_email(message):
    sender = "mizarand@gmail.com"
    app_password = os.environ.get("APP_EMAIL_PASSWORD", "MonitorA2")
    receiver = "mizarand@inbox.lv"

    msg = MIMEText(message)
    msg["Subject"] = "❗ Trader Diary — Ошибка / Обратная связь"
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, receiver, msg.as_string())
    except Exception as e:
        print(f"[Email] Ошибка: {e}")

# Бэкап базы данных

def backup_db():
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_path = f"backup/trader_diary_backup_{now}.db"
    try:
        if not os.path.exists("backup"):
            os.makedirs("backup")
        shutil.copy('trader_diary.db', backup_path)
        print(f"[Бэкап] Скопирована база: {backup_path}")
    except Exception as e:
        print(f"[Бэкап] Ошибка: {e}")

# Подключение к базе данных

def get_db_connection():
    conn = sqlite3.connect('trader_diary.db')
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация базы данных

def init_db():
    conn = sqlite3.connect('trader_diary.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            lot REAL NOT NULL,
            profit REAL NOT NULL,
            comment TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            subject TEXT,
            message TEXT,
            date TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            subscription_status TEXT NOT NULL DEFAULT 'trial',
            trial_start_date TEXT,
            premium_end_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Главная страница
@app.route('/')
def index():
    lang = request.args.get('lang', 'ru')
    texts = translations.get(lang, translations['ru'])
    from datetime import datetime

    try:
        selected_year = int(request.args.get('year', datetime.now().year))
        selected_month = int(request.args.get('month', datetime.now().month))
    except ValueError:
        selected_year = datetime.now().year
        selected_month = datetime.now().month

    current_year = datetime.now().year
    years = list(range(current_year - 4, current_year + 1))
    months = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]

    conn = get_db_connection()
    trades = conn.execute("""
        SELECT * FROM trades
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ORDER BY date DESC
    """, (str(selected_year), f"{selected_month:02d}")).fetchall()
    conn.close()

    total_profit = sum(trade['profit'] for trade in trades)
    profit_by_pair = {}
    for trade in trades:
        profit_by_pair[trade['pair']] = profit_by_pair.get(trade['pair'], 0) + trade['profit']

    return render_template('index.html', trades=trades, total_profit=total_profit,
                           profit_by_pair=profit_by_pair, texts=texts,
                           lang=lang, years=years, months=months,
                           selected_year=selected_year, selected_month=selected_month)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if password != confirm_password:
            flash('❗ Пароли не совпадают.')
            return redirect('/register')

        conn = get_db_connection()
        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing_user:
            flash('❗ Такой логин или email уже зарегистрирован.')
            conn.close()
            return redirect('/register')

        hashed_password = generate_password_hash(password)
        conn.execute("""
            INSERT INTO users (username, email, password_hash, subscription_status, trial_start_date)
            VALUES (?, ?, ?, 'trial', ?)
        """, (username, email, hashed_password, datetime.datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()

        flash('✅ Регистрация прошла успешно! Теперь войдите.')
        return redirect('/login')

    return render_template('register.html')

# Проверка логина
@app.route('/check_user', methods=['POST'])
def check_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?", (username, email)
    ).fetchone()
    conn.close()

    if user:
        return {'exists': True}
    else:
        return {'exists': False}

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['subscription_status'] = user['subscription_status']
            flash(f'Добро пожаловать, {user["username"]}!')
            return redirect('/')
        else:
            flash('Неверный email или пароль.')

    return render_template('login.html')

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.')
    return redirect('/')

# Добавление сделки
@app.route('/add', methods=['POST'])
def add_trade():
    try:
        pair = request.form['pair'].upper()
        date = request.form['date'].replace('T', ' ')
        type_ = request.form['type']
        lot = float(request.form['lot'])
        profit = float(request.form['profit'])
        comment = request.form.get('comment', '')

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO trades (pair, date, type, lot, profit, comment) VALUES (?, ?, ?, ?, ?, ?)',
            (pair, date, type_, lot, profit, comment)
        )
        conn.commit()
        conn.close()

        lang = request.args.get('lang', 'ru')
        return redirect(f"/?lang={lang}")
    except Exception as e:
        send_error_email(f"Ошибка при добавлении сделки:\n{str(e)}")
        return f"Ошибка при добавлении записи: {e}"

# Обратная связь
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    confirmation = ""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO feedback (name, email, subject, message, date) VALUES (?, ?, ?, ?, ?)',
                (name, email, subject, message, date)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            send_error_email(f"[Ошибка при сохранении feedback]\n\n{str(e)}")

        try:
            send_error_email(f"[Обратная связь]\nОт: {name}\nEmail: {email}\nТема: {subject}\n\n{message}")
        except:
            pass

        confirmation = "Спасибо, ваше сообщение отправлено!"

    return render_template('feedback.html', confirmation=confirmation)

# Запуск
if __name__ == "__main__":
    init_db()
    backup_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
