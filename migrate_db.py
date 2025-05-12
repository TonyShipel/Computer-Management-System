from app import app, db
import sqlite3
import os

def migrate_database():
    # Создаем временную таблицу с новой структурой
    with app.app_context():
        # Создаем новую таблицу
        db.engine.execute('''
            CREATE TABLE user_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                face_encoding TEXT,
                credential_id VARCHAR(255) UNIQUE,
                public_key TEXT,
                created_at DATETIME NOT NULL,
                last_login DATETIME
            )
        ''')
        
        # Копируем данные из старой таблицы
        db.engine.execute('''
            INSERT INTO user_new (id, username, face_encoding, created_at, last_login)
            SELECT id, username, face_encoding, created_at, last_login
            FROM user
        ''')
        
        # Удаляем старую таблицу
        db.engine.execute('DROP TABLE user')
        
        # Переименовываем новую таблицу
        db.engine.execute('ALTER TABLE user_new RENAME TO user')
        
        print("Database migration completed successfully")

if __name__ == '__main__':
    migrate_database() 