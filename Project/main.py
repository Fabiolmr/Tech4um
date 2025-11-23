from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import join_room, leave_room, send, SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import random, os
from string import ascii_uppercase

#bibliotecas para autenticação de login
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)

#Configuração do Google OAuth com Flask-Dance
google_bp = make_google_blueprint(
    client_id= os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret= os.environ.get("CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_to="google.login" 
)

app.register_blueprint(google_bp, url_prefix="/login")

# Configuração do Banco de Dados
app.config['SECRET_KEY'] = "DSISHDSHDS"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Inicialização do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modelo User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

#Função par caso o login google dê certo
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Falha ao fazer login com o Google.", category="danger")
        return redirect(url_for("login"))

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Falha ao obter dados do Google.", category="danger")
        return False

    google_user_info = resp.json()
    email = google_user_info["email"]
    name = google_user_info["name"]

    user = User.query.filter_by(username=email).first()

    if user:
        #Usuário existe: Apenas faz o login
        login_user(user)
        flash(f"Login bem-sucedido com Google! Bem-vindo(a), {name}.", category="success")
    else:
        #Usuário novo: Cria e salva o novo usuário no banco de dados
        #Como o login é via OAuth, não precisamos de senha
        new_user = User(username=email, password=generate_password_hash("NO_PASSWORD_NEEDED_OAUTH"))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash(f"Conta criada com Google! Bem-vindo(a), {name}.", category="success")

    return redirect(url_for("home"))

with app.app_context():
    db.create_all()

# SocketIO
socketio = SocketIO(app)

# Sistema de salas
rooms = {}

def generate_unique_code(length):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

# ------ ROTAS DE AUTENTICAÇÃO ------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("As senhas não coincidem!", "danger")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Nome de usuário já existe.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Conta criada com sucesso!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login bem-sucedido!", "success")
            return redirect(url_for("home"))

        flash("Nome de usuário ou senha inválidos.", "danger")
        return redirect(url_for("login"))

    google_login_url = url_for("google.login")

    return render_template("login.html", google_login_url=google_login_url)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado.", "info")
    return redirect(url_for("login"))


# -------------- HOME --------------
@app.route("/", methods=["GET", "POST"])
@login_required
def home():

    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join")
        create = request.form.get("create")

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        # Criar sala
        if create:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}

        # Entrar em sala existente
        elif join:
            if not code:
                return render_template("home.html", error="Please enter a room code", name=name)

            if code not in rooms:
                return render_template("home.html", error="Room does not exist.", name=name)

            room = code

        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))

    return render_template("home.html")


# ----------- SALA DE CHAT ----------
@app.route("/room")
@login_required
def room():
    room = session.get("room")
    name = session.get("name")

    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", room=room, name=name)


# ----------- SOCKET EVENTS ----------
@socketio.on("join")
def handle_join(data):
    room = data["room"]
    username = data["username"]
    join_room(room)
    send(f"{username} entrou na sala.", room=room)


@socketio.on("message")
def handle_message(data):
    room = data["room"]
    username = data["username"]
    message = data["message"]
    send(f"{username}: {message}", room=room)


@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    username = data["username"]
    leave_room(room)
    send(f"{username} saiu da sala.", room=room)


# Inicialização
if __name__ == "__main__":
    socketio.run(app, debug=True)
