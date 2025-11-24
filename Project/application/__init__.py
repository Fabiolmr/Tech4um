from flask import Flask
from flask_socketio import SocketIO

from .extensions import db, login_manager, socketio
from config import Config

from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import google 

socketio = SocketIO()    

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Inicialização das extensões
    socketio.init_app(app)
    db.init_app(app)

    #Models e LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .models.user import User, load_user, google_logged_in # import local


    @login_manager.user_loader
    def user_loader(user_id):
        # Chama a função do seu Model para carregar o usuário
        return load_user(user_id)
    
     # Registro dos seus Blueprints de Controller
    from .controllers.auth import auth_bp  # Suas rotas de login/logout
    from .controllers.main import main_bp # Rotas da homepage
    
    #---------------- autenticação google ---------------------
    google_bp = make_google_blueprint(
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        scope=["profile", "email"],
        redirect_to="chat.home" # Redirecionamento padrão após sucesso
    )
    app.register_blueprint(google_bp, url_prefix="/login/google")

    oauth_authorized.connect(google_logged_in, sender=google_bp)

    from .controllers.auth import auth_bp
    from .controllers.main import main_bp
    from .controllers.chat import chat_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)


    # 3. WebSockets
    from .websockets.handlers import register_socketio_handlers # import local
    register_socketio_handlers(socketio)

    return app