import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Получаем список всех таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Таблицы в базе данных:")
for table in tables:
    print(f"- {table[0]}")
    
    # Получаем структуру таблицы
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print("  Колонки:")
    for col in columns:
        print(f"    {col[1]} ({col[2]})")
    print()

conn.close() 