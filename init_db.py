from app import app, db, User, Computer
from datetime import datetime

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Создаем тестового пользователя
        test_user = User(
            username='test',
            password='test',
            created_at=datetime.utcnow()
        )
        
        # Проверяем, существует ли уже пользователь
        existing_user = User.query.filter_by(username='test').first()
        if not existing_user:
            db.session.add(test_user)
            db.session.commit()
            print("Test user created successfully!")
        else:
            print("Test user already exists!")
        
        # Add test computers if none exist
        if Computer.query.first() is None:
            test_computers = [
                {
                    'name': 'PC-GOGOL-1',
                    'ip_address': '192.186.0.101',
                    'os': 'Windows 10',
                    'room': '101',
                    'user': 'John Doe',
                    'subnet': '192.186.0.1'
                },
                {
                    'name': 'PC-GOGOL-2',
                    'ip_address': '192.186.0.102',
                    'os': 'Windows 11',
                    'room': '102',
                    'user': 'Jane Smith',
                    'subnet': '192.186.0.1'
                },
                {
                    'name': 'PC-KOLYMAZHNY-1',
                    'ip_address': '192.186.1.101',
                    'os': 'Ubuntu 20.04',
                    'room': '201',
                    'user': 'Alice Johnson',
                    'subnet': '192.186.1.1'
                },
                {
                    'name': 'PC-KOLYMAZHNY-2',
                    'ip_address': '192.186.1.102',
                    'os': 'Windows 10',
                    'room': '202',
                    'user': 'Bob Wilson',
                    'subnet': '192.186.1.1'
                }
            ]
            
            for computer_data in test_computers:
                computer = Computer(**computer_data)
                db.session.add(computer)
            
            db.session.commit()
            print("Test computers added successfully")

if __name__ == '__main__':
    init_db() 