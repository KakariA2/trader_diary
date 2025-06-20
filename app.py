from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# Переводы (оставляем как есть — ты уже сделал красиво)
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

def get_db_connection():
    conn = sqlite3.connect('trades.db')
    conn.row_factory = sqlite3.Row
    return conn

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
    pair = request.form['pair']
    date = request.form['date']
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
