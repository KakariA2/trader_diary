@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('trades.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, email, password_hash, subscription_status) VALUES (?, ?, ?, 'trial')", 
                      (username, email, hashed_password))
            conn.commit()
            flash('Регистрация успешна. Войдите в систему.')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Пользователь с таким email или логином уже существует.')
        finally:
            conn.close()

    return render_template('register.html')
