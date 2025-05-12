from app import app, db, User, Computer
import json

# Используем контекст приложения
with app.app_context():
    # Очищаем базу данных
    db.drop_all()
    db.create_all()

    # Загружаем данные из файла
    with open('database_backup.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Импортируем пользователей
    for user_data in data['users']:
        user = User(
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            role=user_data['role'],
            is_active=user_data['is_active']
        )
        db.session.add(user)

    # Импортируем компьютеры
    for computer_data in data['computers']:
        computer = Computer(
            name=computer_data['name'],
            ip_address=computer_data['ip_address'],
            os=computer_data['os'],
            room=computer_data['room'],
            user=computer_data['user'],
            subnet=computer_data['subnet']
        )
        db.session.add(computer)

    # Сохраняем изменения
    db.session.commit()

    print("Данные успешно импортированы в базу данных") 