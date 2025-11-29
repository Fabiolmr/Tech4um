from application.extensions import db, login_manager
from flask_login import UserMixin
from flask import flash, redirect, url_for
from werkzeug.security import generate_password_hash
import secrets

#-----------CLASSE USUÁRIO-------------
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True) # ID agora é numérico e automático
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    avatar_url = db.Column(db.String(500), nullable=True)

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

    user = User.query.filter_by(email=email).first()

    if not user:
        new_user = User(
            email=email, 
            username=name, 
            password=generate_password_hash(secrets.token_urlsafe(32)),
            avatar_url=google_user_info.get("picture") # Tenta pegar a foto do Google
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            user = new_user # Atualiza a variável user para o novo criado
            flash(f"Conta criada com Google! Bem-vindo(a), {name}.", category="success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao criar usuário com Google.", "danger")
            return redirect(url_for("auth.login"))
        
    else:
        flash(f"Login bem-sucedido com Google! Bem-vindo(a), {name}.", category="success")
    
    # 3. Loga o usuário (seja novo ou existente)
    login_user(user)
    return redirect(url_for("main.home"))


