from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from application.models.user import User
from application import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # → Usuário logado não deve ir para /main.home
    # → Deve ir para a área interna (dashboard)
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("As senhas não coincidem!", "danger")
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
    # → Usuário logado deve ir para a página interna (dashboard)
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login bem-sucedido!", "success")
            # após login -> usuário sempre vai pro dashboard (não pro chat)
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
