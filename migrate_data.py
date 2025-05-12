import sqlite3
from app import app, db, Computer

def clean_ip(ip):
    """Очищает и проверяет IP адрес"""
    if not ip:
        return None
    # Убираем лишние пробелы
    ip = ip.strip()
    # Проверяем формат IP
    parts = ip.split('.')
    if len(parts) != 4:
        return None
    try:
        # Проверяем, что все части - числа и в правильном диапазоне
        if all(0 <= int(part) <= 255 for part in parts):
            return ip
    except ValueError:
        pass
    return None

def migrate_table(cursor, table_name, subnet):
    """Мигрирует данные из указанной таблицы"""
    cursor.execute(f'SELECT * FROM {table_name} WHERE name IS NOT NULL OR id IS NOT NULL')
    data = cursor.fetchall()
    
    migrated = 0
    skipped = 0
    
    # Мигрируем данные
    for row in data:
        ip = clean_ip(row[0])  # id содержит IP
        if not ip:
            skipped += 1
            continue
            
        computer = Computer(
            name=row[1] or f"PC-{ip.split('.')[-1]}",  # Если нет имени, используем последний октет IP
            ip_address=ip,
            os=row[4] or "Не указана",
            room=row[2] or "Не указан",
            user=row[3] or "Не указан",
            subnet=subnet
        )
        try:
            # Проверяем, нет ли уже такого IP в базе
            existing = Computer.query.filter_by(ip_address=ip).first()
            if existing:
                print(f"Пропуск: IP {ip} уже существует в базе")
                skipped += 1
                continue
                
            db.session.add(computer)
            db.session.commit()
            migrated += 1
            print(f"Добавлен компьютер: {computer.name} ({computer.ip_address})")
        except Exception as e:
            db.session.rollback()
            skipped += 1
            print(f"Ошибка при добавлении компьютера {ip}: {str(e)}")
    
    return migrated, skipped

def migrate_data():
    # Подключаемся к старой базе данных
    old_conn = sqlite3.connect('data.db')
    old_cursor = old_conn.cursor()
    
    # Создаем контекст приложения
    with app.app_context():
        print("\nМиграция данных с Гоголевского:")
        gog_migrated, gog_skipped = migrate_table(old_cursor, 'gogolevsky', '192.186.0.1')
        
        print("\nМиграция данных с Колымажного:")
        kol_migrated, kol_skipped = migrate_table(old_cursor, 'kolymazhny', '192.186.0.2')
        
        print(f"\nИтоги миграции:")
        print(f"Гоголевский:")
        print(f"  Успешно добавлено: {gog_migrated}")
        print(f"  Пропущено: {gog_skipped}")
        print(f"Колымажный:")
        print(f"  Успешно добавлено: {kol_migrated}")
        print(f"  Пропущено: {kol_skipped}")
        print(f"Всего:")
        print(f"  Успешно добавлено: {gog_migrated + kol_migrated}")
        print(f"  Пропущено: {gog_skipped + kol_skipped}")
    
    # Закрываем соединение со старой базой
    old_conn.close()

def analyze_data():
    """Анализирует данные в таблицах перед миграцией"""
    old_conn = sqlite3.connect('data.db')
    old_cursor = old_conn.cursor()
    
    for table in ['gogolevsky', 'kolymazhny']:
        print(f"\nАнализ данных в таблице {table}:")
        
        # Общее количество записей
        old_cursor.execute(f'SELECT COUNT(*) FROM {table}')
        total = old_cursor.fetchone()[0]
        print(f"Всего записей: {total}")
        
        # Количество записей с именами
        old_cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE name IS NOT NULL AND name != ""')
        with_names = old_cursor.fetchone()[0]
        print(f"Записей с именами: {with_names}")
        
        # Количество записей с IP
        old_cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE id IS NOT NULL AND id != ""')
        with_ip = old_cursor.fetchone()[0]
        print(f"Записей с IP: {with_ip}")
        
        # Примеры валидных записей
        print("\nПримеры записей с данными:")
        old_cursor.execute(f'SELECT * FROM {table} WHERE id IS NOT NULL AND id != "" LIMIT 3')
        for row in old_cursor.fetchall():
            print(f"IP: {row[0]}, Имя: {row[1]}, Кабинет: {row[2]}, Пользователь: {row[3]}, ОС: {row[4]}")
    
    old_conn.close()

if __name__ == '__main__':
    # Анализируем данные
    analyze_data()
    
    # Спрашиваем подтверждение перед миграцией
    response = input('\nНажмите Enter для начала миграции или "n" для отмены: ')
    if response.lower() != 'n':
        migrate_data() 