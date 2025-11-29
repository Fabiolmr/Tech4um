from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from application.models.user import User
from application.extensions import users
import re
#API DE FOTO
import cloudinary
import cloudinary.uploader

#CONFIGURAÇÃO DE API
def configure_cloudinary():
    cloudinary.config(
        cloud_name = "de0mrgc37", # Ou use os.getenv
        api_key = "632973276334999",
        api_secret = "wjlQtLeBDxve3WUEiWkr5792se4"
    )

#VALIDA EMAIL
def is_valid_email(email):
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(padrao, email) is not None

#VARIFICAÇÃO DE SENHA FORTE
def is_strong_password(password):
    #Pelo menos 8 caracteres, uma letra maiúscula, uma minúscula e um dígito.
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

# BLUEPRINT DE AUTENTICAÇÃO
auth_bp = Blueprint('auth', __name__)

# ==========================
#   ROTA AUTENTICAÇÃO
# ==========================

# ROTA CADASTRO
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # SE FOR AUTENTICADO, REDIRECIONA PARA HOME
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == "POST":
        # PEGA VALORES
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        #pega arquivo de foto
        file_avatar = request.files.get("avatar")

        # Verificação se o e-mail é válido
        if not is_valid_email(email):
            flash("E-mail inválido! Digite um endereço válido.", "danger")
            return redirect(url_for("auth.register"))

        # VERIFICA SE SENHAS COINCIDEM
        if password != confirm_password:
            flash("As senhas não coincidem!", "danger")
            return redirect(url_for("auth.register"))
        
        # VERIFICAÇÃO DE FORÇA DA SENHA
        if not is_strong_password(password):
            flash("A senha é muito fraca. Deve ter pelo menos 8 caracteres, incluir letras maiúsculas, minúsculas e números.", "danger")
            return redirect(url_for("auth.register"))
        
        # VERIFICA SE EMAIL JÁ TÁ CADASTRADO
        if any(u.email == email for u in users.values()):
            flash("E-mail já cadastrado.", "danger")
            return redirect(url_for("auth.register"))
        
        #VERIFICA SE NOME JÁ ESTÁ CADASTRADO
        if any(u.username == username for u in users.values()):
            flash("Nome de usuário já existe.", "danger")
            return redirect(url_for("auth.register"))

        # DECLARA LINK DE FOTO
        avatar_url = None

        # SE FOTO FOR INSERIDA
        if file_avatar:
            try: # TENTA USAR A API
                configure_cloudinary() # CONFIGURA AAPI

                upload_result = cloudinary.uploader.upload(
                    file_avatar, folder= "tech4um_profiles",
                    transformation=[
                        # Corta a imagem quadrada focando no rosto automaticamente
                        {'width': 200, 'height': 200, 'gravity': "face", 'crop': "thumb"},
                        {'quality': "auto"} # Otimiza o tamanho do arquivo
                    ]
                )
                # RECEBE URL DA IMAGEM CONFIGURADA
                avatar_url = upload_result['secure_url']
            except Exception as e:
                flash(f"Erro ao enviar imagem: {e}", "danger")
                return redirect(url_for("auth.register"))

        # GERA SENHA HASH
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        # GERA NOVO ID
        new_id = str(len(users) + 1)
        # CRIA NOVO USUÁRIO
        new_user = User(id=new_id, email=email, username=username, password=hashed_password, avatar_url=avatar_url)

        #SALVA NA LISTA GLOBAL DE USUÁRIO
        users[new_id] = new_user

        flash("Conta criada com sucesso!", "success")
        # REDIRECIONA PARA TELA DE LOGIN
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ROTA LOGIN
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # SE JÁ FOR AUTENTICADO, JÁ DIRECIONA PAR HOME
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == "POST":
        # PEGA VALORES DE LOIGN
        identificador = request.form.get("username")
        password = request.form.get("password")

        # PROCURA POR USUÁRIO 
        user = next((u for u in users.values() if u.username == identificador or u.email == identificador), None)
        
        # SE USER É TRUE E AS SENHAS COINCIDEM
        if user and check_password_hash(user.password, password):
            login_user(user) # LOGA USUÁRIO
            flash("Login bem-sucedido!", "success")
            # REDIRECIONA PAR HOME
            return redirect(url_for("main.home"))

        flash("Nome de usuário ou senha inválidos.", "danger")
        return redirect(url_for("auth.login"))

    # PEGA LOGIN DO GOOGLE
    google_login_url = url_for("google.login")

    return render_template("login.html", google_login_url=google_login_url)

# ROTA DE LOGOUT
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user() # DESLOGA USUÁRIO
    flash("Você foi desconectado.", "info")
    #REDIRECIONA PARA HOME
    return redirect(url_for("main.home"))
