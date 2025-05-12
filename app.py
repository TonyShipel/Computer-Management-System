from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import base64
import json
import requests
import time
from functools import wraps
# Временно отключаем ngrok
# from flask_ngrok import run_with_ngrok

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///computers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['OPENROUTER_API_KEY'] = 'OPENROUTER_API_KEY'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Максимальный размер загружаемого файла - 16MB
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Сессия живет 7 дней

# Настройка ngrok - временно отключаем
# ngrok_auth_token = os.getenv('NGROK_AUTH_TOKEN')
# if ngrok_auth_token:
#     app.config['NGROK_AUTH_TOKEN'] = ngrok_auth_token
#     run_with_ngrok(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    chat_history = db.relationship('ChatHistory', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Computer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    os = db.Column(db.String(50), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    user = db.Column(db.String(80), nullable=False)
    subnet = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class ImageGeneration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.String(500), nullable=False)
    style = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Пожалуйста, введите имя пользователя и пароль', 'danger')
            return redirect(url_for('login'))
            
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Ваша учетная запись деактивирована. Обратитесь к администратору.', 'danger')
                return redirect(url_for('login'))
                
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        admin_password = request.form.get('admin_password')
        if admin_password != '777':
            flash('Неверный пароль администратора', 'danger')
            return redirect(url_for('register'))
            
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            flash('Пожалуйста, заполните все поля', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))
            
        user = User(username=username)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Попробуйте позже.', 'danger')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/api/webauthn/register/complete', methods=['POST'])
def webauthn_register_complete():
    data = request.json
    options = session.get('registration_options')
    
    if not options:
        return jsonify({'error': 'Registration session expired'}), 400
        
    # In a real application, you would verify the attestation
    # For this example, we'll just store the credential
    user = User(
        username=data['username'],
        password_hash=data['password'],
        credential_id=data['id'],
        public_key=data['publicKey']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'status': 'ok'})

@app.route('/api/webauthn/authenticate/complete', methods=['POST'])
def webauthn_authenticate_complete():
    data = request.json
    options = session.get('authentication_options')
    
    if not options:
        return jsonify({'error': 'Authentication session expired'}), 400
        
    # In a real application, you would verify the assertion
    user = User.query.filter_by(credential_id=data['id']).first()
    if not user:
        return jsonify({'error': 'Invalid credential'}), 400
        
    login_user(user)
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'status': 'ok'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/api/computers')
@login_required
def get_computers():
    search = request.args.get('search', '').lower()
    subnet = request.args.get('subnet', '')
    
    # Базовый запрос
    query = Computer.query
    
    # Применяем фильтр по subnet, если указан
    if subnet:
        # Для подсети 192.186.0.x
        if subnet == '192.186.0.1':
            query = query.filter(Computer.ip_address.like('192.186.0.%'))
        # Для подсети 192.186.1.x
        elif subnet == '192.186.1.1':
            query = query.filter(Computer.ip_address.like('192.186.1.%'))
    
    # Применяем поиск, если указан
    if search:
        query = query.filter(
            db.or_(
                Computer.name.ilike(f'%{search}%'),
                Computer.ip_address.ilike(f'%{search}%'),
                Computer.os.ilike(f'%{search}%'),
                Computer.room.ilike(f'%{search}%'),
                Computer.user.ilike(f'%{search}%')
            )
        )
    
    # Сортируем по IP-адресу
    # Разбиваем IP на октеты и сортируем численно
    computers = query.all()
    computers.sort(key=lambda x: [int(n) for n in x.ip_address.split('.')])
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'ip_address': c.ip_address,
        'os': c.os,
        'room': c.room,
        'user': c.user,
        'subnet': c.subnet,
        'created_at': c.created_at.isoformat(),
        'updated_at': c.updated_at.isoformat()
    } for c in computers])

@app.route('/api/computer', methods=['POST'])
@login_required
def create_computer():
    try:
        data = request.json
        computer = Computer(
            name=data['name'],
            ip_address=data['ip_address'],
            os=data['os'],
            room=data['room'],
            user=data['user'],
            subnet=data['subnet']
        )
        db.session.add(computer)
        db.session.commit()
        return jsonify({'message': 'Computer created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/computer/<int:id>', methods=['PUT'])
@login_required
def update_computer(id):
    try:
        computer = Computer.query.get_or_404(id)
        data = request.json
        computer.name = data.get('name', computer.name)
        computer.ip_address = data.get('ip_address', computer.ip_address)
        computer.os = data.get('os', computer.os)
        computer.room = data.get('room', computer.room)
        computer.user = data.get('user', computer.user)
        computer.subnet = data.get('subnet', computer.subnet)
        db.session.commit()
        return jsonify({'message': 'Computer updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/computer/<int:id>', methods=['DELETE'])
@login_required
def delete_computer(id):
    try:
        computer = Computer.query.get_or_404(id)
        db.session.delete(computer)
        db.session.commit()
        return jsonify({'message': 'Computer deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/computer/<int:id>', methods=['GET'])
@login_required
def get_computer(id):
    try:
        computer = Computer.query.get_or_404(id)
        return jsonify({
            'id': computer.id,
            'name': computer.name,
            'ip_address': computer.ip_address,
            'os': computer.os,
            'room': computer.room,
            'user': computer.user,
            'subnet': computer.subnet
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.form
        message = data.get('message', '')
        image = request.files.get('image')
        image_path = None
        image_base64 = None
        
        print(f"Received message: {message}")
        
        if image and allowed_file(image.filename):
            filename = f"{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{image.filename}"
            image_path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            image.save(image_path)
            print(f"Image saved to: {image_path}")
            
            # Convert image to base64
            with open(image_path, 'rb') as img:
                image_base64 = base64.b64encode(img.read()).decode('utf-8')
        
        # Получаем последние 5 сообщений для контекста
        chat_history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.created_at.desc()).limit(5).all()
        context = []
        for chat in reversed(chat_history):
            context.extend([
                {"role": "user", "content": chat.message},
                {"role": "assistant", "content": chat.response}
            ])
        
        # Формируем сообщение с учетом изображения
        if image_base64:
            current_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        else:
            current_message = {"role": "user", "content": message}
        
        messages = context + [current_message]
        
        print(f"Prepared messages for API: {json.dumps(messages, indent=2)}")
        
        # Отправляем запрос к OpenRouter
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {app.config['OPENROUTER_API_KEY']}",
            "HTTP-Referer": request.host_url,
            "X-Title": "Computer Management System",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen/qwen2.5-vl-3b-instruct:free",
            "messages": messages,
            "max_tokens": 400
        }
        
        print(f"Sending request to {api_url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        response_data = response.json()
        
        if response.status_code == 200 and 'choices' in response_data:
            gpt_response = response_data['choices'][0]['message']['content']
            
            # Сохраняем историю чата
            chat_history = ChatHistory(
                user_id=current_user.id,
                message=message,
                response=gpt_response,
                image_path=image_path
            )
            db.session.add(chat_history)
            db.session.commit()
            
            return jsonify({
                'response': gpt_response,
                'image_path': image_path
            })
        else:
            error_message = "Ошибка при получении ответа от GPT"
            if 'error' in response_data:
                error_message = f"Ошибка OpenRouter API: {response_data['error'].get('message', 'Неизвестная ошибка')}"
            
            print(f"Error: {error_message}")
            return jsonify({'error': error_message}), 500
            
    except Exception as e:
        import traceback
        error_message = f"Ошибка при обработке запроса: {str(e)}"
        print(f"Exception: {error_message}\n{traceback.format_exc()}")
        return jsonify({'error': error_message}), 500

@app.route('/api/chat/history')
@login_required
def get_chat_history():
    history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.created_at.desc()).all()
    return jsonify([{
        'id': h.id,
        'message': h.message,
        'response': h.response,
        'image_path': h.image_path,
        'created_at': h.created_at.isoformat()
    } for h in history])

class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }
        print(f"Initialized FusionBrainAPI with URL: {url}")

    def get_pipeline(self):
        try:
            response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
            print(f"Pipeline request status code: {response.status_code}")
            data = response.json()
            print(f"Pipeline response: {data}")
            return data[0]['id']
        except Exception as e:
            print(f"Error in get_pipeline: {str(e)}")
            raise

    def generate(self, prompt, pipeline, images=1, width=1024, height=1024):
        try:
            params = {
                "type": "GENERATE",
                "numImages": images,
                "width": width,
                "height": height,
                "generateParams": {
                    "query": f"{prompt}"
                }
            }
            print(f"Generation parameters: {params}")

            data = {
                'pipeline_id': (None, pipeline),
                'params': (None, json.dumps(params), 'application/json')
            }
            
            response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
            print(f"Generation request status code: {response.status_code}")
            
            data = response.json()
            print(f"Generation response: {data}")
            
            return data['uuid']
        except Exception as e:
            print(f"Error in generate: {str(e)}")
            raise

    def check_generation(self, request_id, attempts=10, delay=10):
        attempt = 1
        while attempts > 0:
            try:
                print(f"Checking generation status (attempt {attempt}/{attempts})")
                response = requests.get(self.URL + 'key/api/v1/pipeline/status/' + request_id, headers=self.AUTH_HEADERS)
                print(f"Status check response code: {response.status_code}")
                
                data = response.json()
                print(f"Status check response: {data}")
                
                if data['status'] == 'DONE':
                    if 'result' in data and 'images' in data['result']:
                        return data['result']['images']
                    elif 'result' in data and 'files' in data['result']:
                        return data['result']['files']
                    elif 'images' in data:
                        return data['images']
                    elif 'files' in data:
                        return data['files']
                    else:
                        print(f"Unexpected response structure: {data}")
                        raise Exception("No images or files found in completed response")
                elif data['status'] == 'ERROR':
                    error_msg = data.get('error', 'Unknown error')
                    raise Exception(f"Generation failed: {error_msg}")
                    
            except Exception as e:
                print(f"Error in check_generation: {str(e)}")
                if attempts <= 1:
                    raise
                
            attempts -= 1
            attempt += 1
            time.sleep(delay)
            
        return None

@app.route('/api/generate-image', methods=['POST'])
@login_required
def generate_image():
    data = request.json
    prompt = data.get('prompt')
    style = data.get('style', 'DEFAULT')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
        
    try:
        # Initialize API client
        api = FusionBrainAPI(
            'https://api-key.fusionbrain.ai/',
            '807389EACA86F949497BC77725E33AD1',
            '38AF53E94CCB600B632E7E144555C41A'
        )
        
        # Get pipeline ID
        try:
            pipeline_id = api.get_pipeline()
            print(f"Got pipeline ID: {pipeline_id}")
        except Exception as e:
            print(f"Pipeline Error: {str(e)}")
            return jsonify({'error': 'Failed to get pipeline ID'}), 500
            
        # Start generation
        try:
            uuid = api.generate(f"{prompt} {style}", pipeline_id)
            print(f"Started generation with UUID: {uuid}")
        except Exception as e:
            print(f"Generation Error: {str(e)}")
            return jsonify({'error': 'Failed to start generation'}), 500
            
        # Check generation status and get result
        files = api.check_generation(uuid, attempts=15, delay=10)
        
        if not files:
            return jsonify({'error': 'Generation timeout or failed'}), 500
            
        print(f"Got files: {files}")
            
        # Save the first generated image
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Get the first file data
            image_data = files[0] if isinstance(files, list) else files
            print(f"Image data: {image_data[:100]}...")  # Print first 100 chars for debugging
            
            # Save to file
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f'generated_{timestamp}.png'
            filepath = os.path.join(upload_dir, filename)
            
            # Decode base64 data
            try:
                # Remove header if present
                if isinstance(image_data, str) and 'base64,' in image_data:
                    image_data = image_data.split('base64,')[1]
                
                image_bytes = base64.b64decode(image_data)
                print(f"Decoded image size: {len(image_bytes)} bytes")
                
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                print(f"Image saved successfully to {filepath}")
                
                # Save to database
                image_gen = ImageGeneration(
                    prompt=prompt,
                    style=style,
                    image_url=f'/uploads/{filename}',
                    user_id=current_user.id
                )
                db.session.add(image_gen)
                db.session.commit()
                
                return jsonify({
                    'image_url': f'/uploads/{filename}'
                })
                
            except Exception as e:
                print(f"Error decoding/saving image: {str(e)}")
                return jsonify({'error': f'Failed to decode/save image: {str(e)}'}), 500
            
        except Exception as e:
            print(f"Save Error: {str(e)}")
            return jsonify({'error': f'Failed to save generated image: {str(e)}'}), 500
            
    except Exception as e:
        print(f"General Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/sw.js')
def service_worker():
    response = send_from_directory('static', 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(
            os.path.join(os.getcwd(), 'uploads'),
            filename,
            as_attachment=False,
            mimetype='image/png'
        )
    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('У вас нет прав для доступа к этой странице.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.id).all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    is_active = 'is_active' in request.form
    
    if not username or not password:
        flash('Все поля должны быть заполнены', 'danger')
        return redirect(url_for('manage_users'))
        
    if User.query.filter_by(username=username).first():
        flash('Пользователь с таким именем уже существует', 'danger')
        return redirect(url_for('manage_users'))
        
    user = User(username=username, role=role, is_active=is_active)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        flash('Пользователь успешно добавлен', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при добавлении пользователя', 'danger')
        
    return redirect(url_for('manage_users'))

@app.route('/users/edit', methods=['POST'])
@login_required
@admin_required
def edit_user():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    is_active = 'is_active' in request.form
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id and not is_active:
        flash('Вы не можете деактивировать свой собственный аккаунт', 'danger')
        return redirect(url_for('manage_users'))
        
    if user.id == current_user.id and role != 'admin':
        flash('Вы не можете понизить свои права', 'danger')
        return redirect(url_for('manage_users'))
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user.id:
        flash('Пользователь с таким именем уже существует', 'danger')
        return redirect(url_for('manage_users'))
        
    try:
        user.username = username
        user.role = role
        user.is_active = is_active
        
        if password:
            user.set_password(password)
            
        db.session.commit()
        flash('Пользователь успешно обновлен', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при обновлении пользователя', 'danger')
        
    return redirect(url_for('manage_users'))

@app.route('/users/delete', methods=['POST'])
@login_required
@admin_required
def delete_user():
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Вы не можете удалить свой собственный аккаунт', 'danger')
        return redirect(url_for('manage_users'))
        
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при удалении пользователя', 'danger')
        
    return redirect(url_for('manage_users'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Создаем администратора при первом запуске
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                role='admin',
                is_active=True
            )
            admin_user.set_password('777')
            db.session.add(admin_user)
            db.session.commit()
            print('Администратор успешно создан')
            
    app.run(host='0.0.0.0', port=5000) 
