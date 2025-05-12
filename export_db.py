from app import app, db, User, Computer
import json
from datetime import datetime

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Используем контекст приложения
with app.app_context():
    # Экспорт данных
    data = {
        'users': [],
        'computers': []
    }

    # Экспортируем пользователей
    users = User.query.all()
    for user in users:
        data['users'].append({
            'username': user.username,
            'password_hash': user.password_hash,
            'role': user.role,
            'is_active': user.is_active
        })

    # Экспортируем компьютеры
    computers = Computer.query.all()
    for computer in computers:
        data['computers'].append({
            'name': computer.name,
            'ip_address': computer.ip_address,
            'os': computer.os,
            'room': computer.room,
            'user': computer.user,
            'subnet': computer.subnet
        })

    # Сохраняем в файл
    with open('database_backup.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=serialize_datetime)

    print("База данных успешно экспортирована в database_backup.json") 