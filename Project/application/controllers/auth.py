from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from application.models.user import User
from application import db
import re

def is_strong_password(password):
    """
    Verifica se a senha atende aos critérios de força.
    Pelo menos 8 caracteres, uma letra maiúscula, uma minúscula e um dígito.
    """
    if len(password) < 8:
        return False
    # Pelo menos uma letra maiúscula
    if not re.search(r"[A-Z]", password):
        return False
    # Pelo menos uma letra minúscula
    if not re.search(r"[a-z]", password):
        return False
    # Pelo menos um dígito
    if not re.search(r"\d", password):
        return False
    # Opcional: Adicionar verificação para caractere especial (e.g., r"[!@#$%^&*()]")
    
    return True

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("As senhas não coincidem!", "danger")
            return redirect(url_for("auth.register"))
        
        # VERIFICAÇÃO DE FORÇA DA SENHA
        if not is_strong_password(password):
            flash("A senha é muito fraca. Deve ter pelo menos 8 caracteres, incluir letras maiúsculas, minúsculas e números.", "danger")
            return redirect(url_for("auth.register"))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Nome de usuário já existe.", "danger")
            return redirect(url_for("auth.register"))
        
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Conta criada com sucesso!", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login bem-sucedido!", "success")
            return redirect(url_for("main.home"))

        flash("Nome de usuário ou senha inválidos.", "danger")
        return redirect(url_for("auth.login"))

    google_login_url = url_for("google.login")

    return render_template("login.html", google_login_url=google_login_url)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado.", "info")
    return redirect(url_for("auth.login"))
