from application.extensions import login_manager, users
from flask_login import UserMixin
from flask import flash, redirect, url_for
from werkzeug.security import generate_password_hash
from flask_dance.contrib.google import google

#-----------CLASSE USUÁRIO-------------
class User(UserMixin):
    def __init__(self, id, email, username, password, avatar_url=None):
        self.id = str(id)
        self.email = email
        self.username = username
        self.password = password
        self.avatar_url = avatar_url

# Loader para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id) #RETORNA USUÁRIO


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

    user = next((u for u in users.values() if u.email == email), None)

    if not user:
        new_id = str(len(users) + 1)
        new_user = User(id=new_id, email=email, username=name, password=generate_password_hash("OAUTH_LOGIN"))
        users[new_id] = new_user
        user = new_user
        flash(f"Conta criada com Google! Bem-vindo(a), {name}.", category="success")
    else:
        flash(f"Login bem-sucedido com Google! Bem-vindo(a), {name}.", category="success")
    
    login_user(user)
    return redirect(url_for("chat.home"))


