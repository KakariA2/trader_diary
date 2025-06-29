import smtplib
from email.mime.text import MIMEText

sender = "your_email@gmail.com"  # <-- здесь твой Gmail
recipient = "тоже_твой_email@gmail.com"  # <-- на какой email проверить
password = "16-значный пароль приложения"  # <-- пароль из Gmail, а не обычный

msg = MIMEText("Проверка отправки письма")
msg["Subject"] = "Тестовое письмо"
msg["From"] = sender
msg["To"] = recipient

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print("✅ Письмо успешно отправлено.")
except Exception as e:
    print("❌ Ошибка при отправке письма:", e)
