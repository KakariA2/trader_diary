from flask import Flask, render_template, request, redirect
import sqlite3
import os

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

# Подключение к БД
def get_db_connection():
    conn = sqlite3.connect('trades.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создание таблицы, если нет
def init_db():
    conn = get_db_connection()
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
    conn.commit()
    conn.close()

@app.route('/', methods=['GET'])
def index():
    lang = request.args.get('lang', 'ru')
    texts = translations.get(lang, translations['ru'])

    conn = get_db_connection()
    trades = conn.execute('SELECT * FROM trades ORDER BY id DESC').fetchall()
    conn.close()

    total_profit = sum(trade['profit'] for trade in trades)

    profit_by_pair = {}
    for trade in trades:
        pair = trade['pair']
        profit_by_pair[pair] = profit_by_pair.get(pair, 0) + trade['profit']

    return render_template('index.html',
                           trades=trades,
                           total_profit=total_profit,
                           profit_by_pair=profit_by_pair,
                           texts=texts,
                           lang=lang)

@app.route('/add', methods=['POST'])
def add_trade():
    try:
        pair = request.form['pair']
        date = request.form['date'].replace('T', ' ')  # преобразуем ISO в читаемый формат
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
        return f"Ошибка при добавлении записи: {e}"

if __name__ == "__main__":
    init_db()  # создаём таблицу при старте, если её нет
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
