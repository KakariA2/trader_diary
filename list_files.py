import os

print("📂 Файлы в текущей папке проекта:")
for file in os.listdir():
    print(" -", file)