from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from application.extensions import rooms, generate_unique_code, socketio
from application.models.forum import Forum
from application.models.user import User
from application.websockets.handlers import get_participantes_list

main_bp = Blueprint('main', __name__)

# ==========================
#   PARTE: USUÁRIOS ONLINE
# ==========================

online_users = set()

@socketio.on("connect")
def handle_connect():
    if current_user.is_authenticated:
        online_users.add(current_user.username)

    socketio.emit("online_users", list(online_users))


@socketio.on("disconnect")
def handle_disconnect():
    if current_user.is_authenticated:
        online_users.discard(current_user.username)

    socketio.emit("online_users", list(online_users))


# ==========================
#   ROTA HOME
# ==========================

@main_bp.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        create_name = request.form.get("create_name")
        create_desc = request.form.get("create-desc")

        # ------------ Criar novo fórum ------------
        if create_name:
            # Verifica login
            if not current_user.is_authenticated:
                flash("Você precisa estar logado para criar uma sala.", "danger")
                return redirect(url_for("auth.login"))

            new_id = generate_unique_code(4)

            # Novo fórum
            new_forum = Forum(new_id, create_name, create_desc, current_user.username)
            rooms[new_id] = new_forum

            socketio.emit("new_room", {
                "id": new_id,
                "name": create_name,
                "description": create_desc,
                "creator": current_user.username
            })

            return redirect(url_for("chat.access_forum", forum_id=new_id))

        # ------------- Entrar em fórum existente -------------
        code = request.form.get("entrar")
        if code in rooms:
            return redirect(url_for("chat.access_forum", forum_id=code))

    return render_template("home.html", rooms=rooms.values())


# ==========================
#   ROTA MEMBROS    
# ==========================

@main_bp.route("/join_member/<forum_id>", methods=["POST"])
@login_required
def join_member(forum_id):
    if forum_id in rooms:
        rooms[forum_id].add_member(current_user.username)
        flash(f"Agora você é membro do fórum {rooms[forum_id].name}!", "success")
        socketio.emit("users_list", get_participantes_list(forum_id), room=forum_id)

        socketio.emit("update_member_count", {
            "forum_id": forum_id,
            "count": len(rooms[forum_id].members)
        })
    else:
        flash("Fórum não encontrado.", "danger")
    
    return redirect(url_for("main.home"))

@main_bp.route("/leave_member/<forum_id>", methods=["POST"])
@login_required
def leave_member(forum_id):
    if forum_id in rooms:
        rooms[forum_id].remove_member(current_user.username)
        flash(f"Você saiu do fórum {rooms[forum_id].name}.", "info")
        socketio.emit("users_list", get_participantes_list(forum_id), room=forum_id)

        socketio.emit("update_member_count", {
            "forum_id": forum_id,
            "count": len(rooms[forum_id].members)
        })
        
    return redirect(url_for("main.home"))

@main_bp.route("/perfil/<username>")
def perfil(username):
    
    
    user_data = {
        'username': username,
        'bio': f"Este é o perfil de {username}. Detalhes da bio viriam do DB.",
        # Adicione outros dados (ex: foto, data de registro, etc.)
    }

    
    return render_template("perfil.html", user=user_data) # Mude user_data para user se usar o modelo

@main_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required 
def edit_profile():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")

        # 1. Verificar a senha atual
        if not check_password_hash(current_user.password, current_password):
            flash("Senha atual incorreta.", "danger")
            return redirect(url_for('main.edit_profile'))

        # 2. Verificar se o novo username/email já está em uso por OUTRO usuário
        # ... (Lógica de verificação, garantindo que não seja o próprio current_user)

        # 3. Processar a alteração de senha (se houver)
        if new_password:
            if new_password != confirm_new_password:
                flash("A nova senha e a confirmação não coincidem.", "danger")
                return redirect(url_for('main.edit_profile'))
            
            # Use a função is_strong_password que você definiu
            # if not is_strong_password(new_password):
            #     flash("A nova senha é muito fraca...", "danger")
            #     return redirect(url_for('main.edit_profile'))
            
            # Se tudo estiver ok, faça o hash e atualize:
            current_user.password = generate_password_hash(new_password, method="pbkdf2:sha256")

        # 4. Atualizar username e email
        current_user.username = username
        current_user.email = email
        
        # 5. Salvar as alterações no seu 'users' dictionary/database
        # users[current_user.id] = current_user 

        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for('main.profile'))

    return render_template("edit_profile.html")