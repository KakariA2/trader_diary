import 'package:flutter/material.dart';

void main() => runApp(TraderDiaryApp());

class TraderDiaryApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trader Diary',
      home: DiaryPage(),
    );
  }
}

class DiaryPage extends StatefulWidget {
  @override
  _DiaryPageState createState() => _DiaryPageState();
}

class _DiaryPageState extends State<DiaryPage> {
  final _formKey = GlobalKey<FormState>();
  final List<Map<String, dynamic>> trades = [];

  String instrument = 'EUR/USD';
  String type = 'Buy';
  String lot = '';
  String entry = '';
  String sl = '';
  String tp = '';
  String comment = '';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Дневник трейдера')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Form(
              key: _formKey,
              child: Column(children: [
                Row(children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: instrument,
                      items: ['EUR/USD', 'GBP/USD', 'XAU/USD', 'BTC/USD']
                          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                          .toList(),
                      onChanged: (val) => setState(() => instrument = val!),
                      decoration: InputDecoration(labelText: 'Инструмент'),
                    ),
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      value: type,
                      items: ['Buy', 'Sell']
                          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                          .toList(),
                      onChanged: (val) => setState(() => type = val!),
                      decoration: InputDecoration(labelText: 'Тип'),
                    ),
                  ),
                ]),
                Row(children: [
                  Expanded(
                    child: TextFormField(
                      decoration: InputDecoration(labelText: 'Лот'),
                      keyboardType: TextInputType.number,
                      onChanged: (val) => lot = val,
                    ),
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: TextFormField(
                      decoration: InputDecoration(labelText: 'Вход'),
                      keyboardType: TextInputType.number,
                      onChanged: (val) => entry = val,
                    ),
                  ),
                ]),
                Row(children: [
                  Expanded(
                    child: TextFormField(
                      decoration: InputDecoration(labelText: 'SL'),
                      keyboardType: TextInputType.number,
                      onChanged: (val) => sl = val,
                    ),
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: TextFormField(
                      decoration: InputDecoration(labelText: 'TP'),
                      keyboardType: TextInputType.number,
                      onChanged: (val) => tp = val,
                    ),
                  ),
                ]),
                TextFormField(
                  decoration: InputDecoration(labelText: 'Комментарий'),
                  onChanged: (val) => comment = val,
                ),
                SizedBox(height: 10),
                ElevatedButton(
                  onPressed: () {
                    if (_formKey.currentState!.validate()) {
                      setState(() {
                        trades.add({
                          'instrument': instrument,
                          'type': type,
                          'lot': lot,
                          'entry': entry,
                          'sl': sl,
                          'tp': tp,
                          'comment': comment,
                          'time': DateTime.now(),
                        });
                      });
                    }
                  },
                  child: Text('Сохранить сделку'),
                ),
              ]),
            ),
            Divider(height: 20),
            Expanded(
              child: ListView.builder(
                itemCount: trades.length,
                itemBuilder: (context, index) {
                  final trade = trades[index];
                  return Card(
                    child: ListTile(
                      title: Text('${trade['instrument']} | ${trade['type']} | Лот: ${trade['lot']}'),
                      subtitle: Text(
                        'Вход: ${trade['entry']} | SL: ${trade['sl']} | TP: ${trade['tp']}\n'
                        'Комментарий: ${trade['comment']}\n'
                        'Дата: ${trade['time'].toString().split('.')[0]}',
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
