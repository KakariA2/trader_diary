from flask import Flask, render_template, request, redirect
import sqlite3
import os
import shutil
import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

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

# Отправка email при ошибках и для обратной связи
def send_error_email(message):
    sender = "mizarand@gmail.com"
    app_password = "MonitorA2"
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
        print(f"[Email] Ошибка при отправке письма: {e}")

# Создание бэкапа базы данных
def backup_db():
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_path = f"backup/trader_diary_backup_{now}.db"
    try:
        if not os.path.exists("backup"):
            os.makedirs("backup")
        shutil.copy('trader_diary.db', backup_path)
        print(f"[Бэкап] Сохранена копия базы: {backup_path}")
    except Exception as e:
        print(f"[Бэкап] Ошибка при создании бэкапа: {e}")

# Подключение к базе
def get_db_connection():
    conn = sqlite3.connect('trader_diary.db')
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация базы
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
    conn.commit()
    conn.close()

# Главная страница с фильтром по году и месяцу
@app.route('/', methods=['GET'])
def index():
    lang = request.args.get('lang', 'ru')
    texts = translations.get(lang, translations['ru'])

    # Получаем год и месяц из параметров GET
    year = request.args.get('year')
    month = request.args.get('month')

    now = datetime.datetime.now()
    if not year or not year.isdigit():
        year = now.year
    else:
        year = int(year)

    if not month or not month.isdigit():
        month = now.month
    else:
        month = int(month)

    # Формируем даты для фильтрации
    start_date = f"{year}-{month:02d}-01 00:00"
    if month == 12:
        end_year = year + 1
        end_month = 1
    else:
        end_year = year
        end_month = month + 1
    end_date = f"{end_year}-{end_month:02d}-01 00:00"

    conn = get_db_connection()
    trades = conn.execute(
        "SELECT * FROM trades WHERE date >= ? AND date < ? ORDER BY date DESC",
        (start_date, end_date)
    ).fetchall()
    conn.close()

    total_profit = sum(trade['profit'] for trade in trades)
    profit_by_pair = {}
    for trade in trades:
        pair = trade['pair']
        profit_by_pair[pair] = profit_by_pair.get(pair, 0) + trade['profit']

    years = list(range(2020, now.year + 1))

    return render_template('index.html',
                           trades=trades,
                           total_profit=total_profit,
                           profit_by_pair=profit_by_pair,
                           texts=texts,
                           lang=lang,
                           years=years,
                           selected_year=year,
                           selected_month=month)

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
