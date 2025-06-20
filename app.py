from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Обновлённые переводы
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
    },
    'en': {
        'title': 'Trader Diary',
        'total_profit': 'Total Profit/Loss',
        'profit_by_pair': 'Profit by Currency Pair',
        'pair': 'Pair',
        'date': 'Date',
        'type': 'Type',
        'lot': 'Lot',
        'profit_loss': 'Profit/Loss',
        'comment': 'Comment',
        'buy': 'Buy',
        'sell': 'Sell',
        'save': '💾 Save',
        'support': 'Buy me a coffee for a lucky trade',
        'buymeacoffee': 'Buymeacoffee',
        'paypal': 'PayPal',
        'boosty': 'Boosty',
    },
    'es': {
        'title': 'Diario del Trader',
        'total_profit': 'Ganancia/Pérdida Total',
        'profit_by_pair': 'Ganancia por Par de Divisas',
        'pair': 'Par',
        'date': 'Fecha',
        'type': 'Tipo',
        'lot': 'Lote',
        'profit_loss': 'Ganancia/Pérdida',
        'comment': 'Comentario',
        'buy': 'Compra',
        'sell': 'Venta',
        'save': '💾 Guardar',
        'support': 'Invítame un café por una operación exitosa',
        'buymeacoffee': 'Buymeacoffee',
        'paypal': 'PayPal',
        'boosty': 'Boosty',
    },
    'pt': {
        'title': 'Diário do Trader',
        'total_profit': 'Lucro/Prejuízo Total',
        'profit_by_pair': 'Lucro por Par de Moedas',
        'pair': 'Par',
        'date': 'Data',
        'type': 'Tipo',
        'lot': 'Lote',
        'profit_loss': 'Lucro/Prejuízo',
        'comment': 'Comentário',
        'buy': 'Compra',
        'sell': 'Venda',
        'save': '💾 Salvar',
        'support': 'Me pague um café por uma negociação de sucesso',
        'buymeacoffee': 'Buymeacoffee',
        'paypal': 'PayPal',
        'boosty': 'Boosty',
    },
}

trades = []

@app.route('/', methods=['GET'])
def index():
    lang = request.args.get('lang', 'ru')
    if lang not in translations:
        lang = 'ru'
    texts = translations[lang]

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

    trades.insert(0, {  # Новая запись добавляется в начало списка
        'pair': pair,
        'date': date,
        'type': type_,
        'lot': lot,
        'profit': profit,
        'comment': comment
    })

    lang = request.args.get('lang', 'ru')
    return redirect(f"/?lang={lang}")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
