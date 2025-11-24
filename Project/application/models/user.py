from application.extensions import db, login_manager
from flask_login import UserMixin
from flask import flash, redirect, url_for
from werkzeug.security import generate_password_hash
from flask_dance.contrib.google import google

#-----------CLASSE USUÁRIO-------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False) # Armazena o hash


# Loader para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) #RETORNA USUÁRIO


# Função par caso o login google dê certo
def google_logged_in(blueprint, token):
    from flask_login import login_user # Import local para evitar circular
    
    if not token:
        flash("Falha ao fazer login com o Google.", category="danger")
        return redirect(url_for("auth.login"))

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Falha ao obter dados do Google.", category="danger")
        return False

    google_user_info = resp.json()
    email = google_user_info["email"]
    name = google_user_info["name"]

    user = User.query.filter_by(username=email).first()

    if user:
        login_user(user)
        flash(f"Login bem-sucedido com Google! Bem-vindo(a), {name}.", category="success")
    else:
        new_user = User(username=email, password=generate_password_hash("NO_PASSWORD_NEEDED_OAUTH"))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash(f"Conta criada com Google! Bem-vindo(a), {name}.", category="success")

    return redirect(url_for("chat.home")) # Usamos chat.home agora


