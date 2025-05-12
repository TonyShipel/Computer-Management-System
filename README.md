# Computer Management System

A web application for managing computers in different subnets with face recognition authentication and GPT chat integration.

## Features

- Face recognition authentication
- Computer management for two subnets (192.186.0.1 and 192.186.1.1)
- Search functionality for computers
- GPT chat with image upload capability and multiple AI model support
- Mobile-responsive design

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Webcam for face recognition
- OpenRouter API key for GPT functionality
- [Pillow](https://python-pillow.org) (для генерации иконок)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following content:
```
SECRET_KEY=your-secret-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here
```

5. Create the uploads directory for chat images:
```bash
mkdir uploads
```

## Usage

### Запуск основного приложения

```bash
python app.py
```

Приложение будет доступно по адресу: http://localhost:5000

### Генерация иконок для сайта

```bash
python create_icons.py
```

Иконки появятся в папке `static/icons`.

### Инициализация и тестовые данные

```bash
python init_db.py
```

### Экспорт БД в JSON

```bash
python export_db.py
```

### Импорт БД из JSON

```bash
python import_db.py
```

### Миграция данных из сторонних таблиц (пример)

```bash
python migrate_data.py
```

### Примечания
- Для работы face recognition требуется вебкамера.
- Для GPT-чата необходим API-ключ OpenRouter.
- Все переменные окружения можно задать в файле `.env` в корне проекта.
- Для production-релиза рекомендуется запуск через gunicorn (см. gunicorn_config.py).

## First-time setup: регистрация пользователя с FaceID

Для первой регистрации пользователя с FaceID используйте консоль Python:

```python
from app import app, db, User
import face_recognition
import os

with app.app_context():
    # Create a test user
    image = face_recognition.load_image_file("path_to_face_image.jpg")
    face_encoding = face_recognition.face_encodings(image)[0]
    
    user = User(
        username="test_user",
        face_encoding=str(face_encoding.tolist())
    )
    
    db.session.add(user)
    db.session.commit()
```

## Features in Detail

### Computer Management
- View computers in two different subnets
- Search computers by IP, name, room, or user
- Edit computer details
- Responsive card layout for easy viewing on mobile devices

### Face Recognition
- Secure login using facial recognition
- Works with most modern webcams
- Real-time face detection and matching

### GPT Chat
- Interactive chat interface with multiple AI models
- Support for image uploads
- Chat history preservation per user
- Context-aware responses
- Model selection (GPT-3.5, GPT-4, Claude 2, PaLM 2, Llama 2)

## Security Notes

- The application uses face recognition for authentication
- All sensitive data is stored securely in the database
- API keys and secrets are managed through environment variables
- Face recognition data is stored as encrypted encodings

## Troubleshooting

1. Face Recognition Issues:
   - Ensure good lighting conditions
   - Position your face properly in front of the camera
   - Try registering your face again if recognition fails

2. Database Issues:
   - If the database is corrupted, delete the `computers.db` file and restart the application
   - The database will be automatically recreated

3. GPT Chat Issues:
   - Verify your OpenRouter API key is correct in the `.env` file
   - Check your internet connection
   - Ensure the image file size is not too large
   - If a specific model is not working, try selecting a different one

## OpenRouter Setup

1. Sign up for an account at [OpenRouter](https://openrouter.ai/)
2. Get your API key from the dashboard
3. Add the API key to your `.env` file as `OPENROUTER_API_KEY`
4. The application supports multiple models through OpenRouter:
   - GPT-3.5 Turbo
   - GPT-4
   - Claude 2
   - PaLM 2
   - Llama 2 70B

## Contributing

Feel free to submit issues and enhancement requests! 
