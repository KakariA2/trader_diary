import os
import smtplib
from email.mime.text import MIMEText

sender = "mizarand@gmail.com"
password = os.getenv("APP_EMAIL_PASSWORD")
receiver = "твой_адрес_почты@gmail.com"

msg = MIMEText("Тестовое сообщение из Flask-приложения.")
msg['Subject'] = "Тест SMTP"
msg['From'] = sender
msg['To'] = receiver

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
    print("Письмо отправлено успешно!")
except Exception as e:
    print(f"Ошибка при отправке письма: {e}")
