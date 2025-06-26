from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
import os
import shutil
import datetime
import smtplib
import uuid
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'trader_diary_secret_key'

# ==================== БАЗА ДАННЫХ ====================
def get_db_connection():
    conn = sqlite3.connect('trader_diary.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            subscription_status TEXT NOT NULL DEFAULT 'trial',
            trial_start_date TEXT,
            premium_end_date TEXT,
            is_verified INTEGER DEFAULT 0,
            verification_token TEXT
        )
    ''')
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
    conn.commit()
    conn.close()

# ==================== EMAIL ====================
def send_email(to_email, subject, message_body):
    sender = "mizarand@gmail.com"
    app_password = "yiakaceuukylohfz" #app_password = os.environ.get("APP_EMAIL_PASSWORD", "MonitorA2")   Лучше хранить пароль в переменных окружения!

    msg = MIMEText(message_body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, to_email, msg.as_string())
        print("✅ Email отправлен.")
    except Exception as e:
        print(f"❌ Ошибка email: {e}")

# ==================== BACKUP ====================
def backup_db():
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_path = f"backup/trader_diary_backup_{now}.db"
    if not os.path.exists("backup"):
        os.makedirs("backup")
    shutil.copy('trader_diary.db', backup_path)
    print(f"[Бэкап] Скопирована база: {backup_path}")

# ==================== РОУТЫ ====================

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    trades = conn.execute('SELECT * FROM trades ORDER BY date DESC').fetchall()
    conn.close()

    total_profit = sum(t['profit'] for t in trades)
    return render_template('index.html', trades=trades, total_profit=total_profit)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("❗ Пароли не совпадают.")
            return redirect('/register')

        conn = get_db_connection()
        existing = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
        if existing:
            flash("❗ Такой логин или email уже зарегистрирован.")
            conn.close()
            return redirect('/register')

        hashed = generate_password_hash(password)
        token = str(uuid.uuid4())

        conn.execute('''
            INSERT INTO users (username, email, password_hash, subscription_status, trial_start_date, verification_token)
            VALUES (?, ?, ?, 'trial', ?, ?)
        ''', (username, email, hashed, datetime.datetime.now().strftime('%Y-%m-%d'), token))
        conn.commit()
        conn.close()

        verify_link = f"http://localhost:5000/verify/{token}"
        send_email(email, "Подтвердите регистрацию", f"Здравствуйте, {username}!\n\nПерейдите по ссылке для подтверждения: {verify_link}")

        flash("✅ Регистрация прошла успешно. Проверьте почту для подтверждения.")
        return redirect('/login')
    return render_template('register.html')

@app.route('/verify/<token>')
def verify_email(token):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE verification_token = ?", (token,)).fetchone()
    if user:
        if user["is_verified"]:
            flash("Ваш email уже подтверждён.")
        else:
            conn.execute("UPDATE users SET is_verified = 1, verification_token = NULL WHERE id = ?", (user['id'],))
            conn.commit()
            flash("✅ Email успешно подтверждён.")
    else:
        flash("❌ Неверная или устаревшая ссылка.")
    conn.close()
    return redirect('/login')

@app.route('/check_user', methods=['POST'])
def check_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
    conn.close()

    return jsonify({'exists': bool(user)})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_verified']:
                flash("Пожалуйста, подтвердите свой email.")
                return redirect('/login')

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['subscription_status'] = user['subscription_status']
            flash(f"Добро пожаловать, {user['username']}!")
            return redirect('/')
        else:
            flash("Неверный email или пароль.")
    return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.clear()
    flash("Вы вышли из системы.")
    return redirect('/login')
    
    @app.route('/reset_db')
def reset_db():
    import os
    if os.path.exists('users.db'):
        os.remove('users.db')
    import init_db  # если у тебя есть файл init_db.py для создания базы
    return '✅ База данных успешно очищена.'

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Пожалуйста, войдите в систему.")
        return redirect('/login')
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

# =============== ЗАПУСК ===============
if __name__ == '__main__':
    init_db()
    backup_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
