from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_avatars import Avatars

# Inicializamos as extensões aqui
db = SQLAlchemy() #BANCO DE DADOS (FUTURAMENTE IMPLEMENTADO)
login_manager = LoginManager()
socketio = SocketIO() #COMUNICAÇÃO SOCKET
avatars = Avatars() #API AVATAR

online_users = set()

# Função para criar código de fórum
from string import ascii_uppercase
import random

def generate_unique_code(length):
        return "".join(random.choice(ascii_uppercase) for _ in range(length))