from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

# Inicializamos as extensões aqui, mas sem vincular ao "app" ainda
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

# Variável global para armazenar salas criadas dinamicamente (se houver)
rooms = {}

# Função de utilidade
from string import ascii_uppercase
import random
def generate_unique_code(length):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code