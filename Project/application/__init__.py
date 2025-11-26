from flask import Flask
from flask_dance.contrib.google import google, make_google_blueprint
from flask_dance.consumer import oauth_authorized
from config import Config

from application.extensions import login_manager, socketio


def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )

    app.config.from_object(Config)

    # Inicialização das extensões
    socketio.init_app(app)

    # Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .models.user import google_logged_in

    # 1. Blueprints normais
    from .controllers.main import main_bp      # Home / Página inicial
    from .controllers.auth import auth_bp      # Login / Registro
    from .controllers.chat import chat_bp      # Chat

    # 2. Blueprint do Google OAuth
    google_bp = make_google_blueprint(
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        scope=["profile", "email"],
        redirect_to="chat.home"
    )

    app.register_blueprint(google_bp, url_prefix="/login/google")
    oauth_authorized.connect(google_logged_in, sender=google_bp)

    # 3. Registrar os seus próprios blueprints
    app.register_blueprint(main_bp)   # "/" home.html
    app.register_blueprint(auth_bp)   # "/login", "/register"
    app.register_blueprint(chat_bp)   # "/chat"

    # 4. WebSockets
    from .websockets.handlers import register_socketio_handlers
    register_socketio_handlers(socketio)

    return app
