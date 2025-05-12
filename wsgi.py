import sys
import os

# Добавляем путь к приложению в Python path
sys.path.insert(0, '/var/www/pyip')

# Активируем виртуальное окружение
activate_this = '/var/www/pyip/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Импортируем приложение
from app import app as application 