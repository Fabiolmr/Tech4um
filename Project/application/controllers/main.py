from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required, logout_user
from application.extensions import rooms, generate_unique_code, socketio, users
from application.models.forum import Forum
from application.models.user import User
from application.websockets.handlers import get_participantes_list
from werkzeug.security import check_password_hash, generate_password_hash

#CRIA BLUEPRINT PRA MAIN
main_bp = Blueprint('main', __name__)

# ==========================
#   PARTE: USUÁRIOS ONLINE
# ==========================

#LISTA DE USUÁRIOS ONLINE
online_users = set()

#ROTA CONNECT
@socketio.on("connect")
def handle_connect():
    #SE O USUÁRIO ESTIVER AUTENTICADO
    if current_user.is_authenticated:
        #ADICIONA USUÁRIO ATUAL NA LISTA
        online_users.add(current_user.username)

    socketio.emit("online_users", list(online_users))

#ROTA DISCONNECT
@socketio.on("disconnect")
def handle_disconnect():
    #SE O USUÁRIO ESTÁ AUTENTICADO
    if current_user.is_authenticated:
        #RETIRA DA LISTA
        online_users.discard(current_user.username)

    socketio.emit("online_users", list(online_users))


# ==========================
#   ROTA HOME
# ==========================

@main_bp.route("/", methods=["GET", "POST"])
def home():
    #SE FOR METODO POST (RECEBE VALORES)
    if request.method == "POST":
        create_name = request.form.get("create_name") #SALVA NOME
        create_desc = request.form.get("create-desc") #SALVA DESCRIÇÃO

        # ------------ Criar novo fórum ------------
        if create_name:
            # SE USUÁRIO NÃO ESTÁ AUTENTICADO, REDIRECIONA PARA ROTA DE LOGIN
            if not current_user.is_authenticated:
                flash("Você precisa estar logado para criar uma sala.", "danger")
                return redirect(url_for("auth.login"))

            # VERIFICA SE NOME DO FÓRUM JÁ ESTÁ EM USO
            for forum in rooms.values():
                if create_name == forum.name:
                    flash("Nome de fórum já está em uso", "danger")
                    return redirect(url_for("main.home"))
            
            #NOVO CÓDIGO
            new_id = generate_unique_code(4)
            
            # NOVO FÓRUM
            new_forum = Forum(new_id, create_name, create_desc, current_user.username)
            #SALVA NOVO FÓRUM NA POSIÇÃO COM NOVO ID
            rooms[new_id] = new_forum


            socketio.emit("new_room", {
                "id": new_id,
                "name": create_name,
                "description": create_desc,
                "creator": current_user.username
            })

            # REDIRECIONA PARA ROTA DE ACESSAR FORUM
            return redirect(url_for("chat.access_forum", forum_id=new_id))


        # ------------- Entrar em fórum existente -------------
        code = request.form.get("entrar") #RECEBE AÇÃO DO BOTÃO ENTRAR
        if code in rooms:
            return redirect(url_for("chat.access_forum", forum_id=code))
    

    return render_template("home.html", rooms=rooms.values())


# ==========================
#   ROTA MEMBROS    
# ==========================

# ROTA PARA SER MEMBRO
@main_bp.route("/join_member/<forum_id>", methods=["POST"])
@login_required # INDICA QUE PRECISA ESTAR LOGADO
def join_member(forum_id):
    if forum_id in rooms:
        # ADICONA USUÁRIO ATUAL NA LISTA DE MEMBROS
        rooms[forum_id].add_member(current_user.username)
        flash(f"Agora você é membro do fórum {rooms[forum_id].name}!", "success")

        socketio.emit("users_list", get_participantes_list(forum_id), room=forum_id)

        socketio.emit("update_member_count", {
            "forum_id": forum_id,
            "count": len(rooms[forum_id].members)
        })
    else:
        flash("Fórum não encontrado.", "danger")
    
    # REDIRECIONA PARA HOME
    return redirect(url_for("main.home"))

#ROTA PARA DEIXAR DE SER MEMBRO
@main_bp.route("/leave_member/<forum_id>", methods=["POST"])
@login_required #AUTENTICAÇÃO NECESSÁRIA
def leave_member(forum_id):
    if forum_id in rooms:
        #REMOVE USUÁRIO ATUAL DA LISTA DE  MEMBROS
        rooms[forum_id].remove_member(current_user.username)
        flash(f"Você saiu do fórum {rooms[forum_id].name}.", "info")
        socketio.emit("users_list", get_participantes_list(forum_id), room=forum_id)

        socketio.emit("update_member_count", {
            "forum_id": forum_id,
            "count": len(rooms[forum_id].members)
        })
        
        
    return redirect(url_for("main.home"))

# ==========================
#   ROTA PERFIL    
# ==========================

@main_bp.route("/perfil")
@login_required 
def perfil():
    #REDIRECIONA PARA TELA DE PERFIL  
    return render_template("perfil.html")

 
#ROTA PAR EDITR PERFIL
@main_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required 
def edit_profile():
    if request.method == "POST":
        # PEGA NOVOS VALORES INSERIDOS
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")

        # VERIFICA SENHA DE CONFIRMAÇÃO
        if not check_password_hash(current_user.password, current_password):
            flash("Senha atual incorreta. As alterações não foram salvas.", "danger")
            return redirect(url_for('main.edit_profile'))

        # VERIFICA SE NOME E EMAIL JÁ ESTÁ EM USO
        for user_id, user_obj in users.items(): 
            if user_id != current_user.id:
                if user_obj.username == username:
                    flash("Nome de usuário já está em uso.", "danger")
                    return redirect(url_for('main.edit_profile'))
                
                if user_obj.email == email:
                    flash("E-mail já está em uso.", "danger")
                    return redirect(url_for('main.edit_profile'))


        # PROCESSAR A NOVA SENHA
        if new_password:
            if new_password != confirm_new_password:
                flash("A nova senha e a confirmação não coincidem.", "danger")
                return redirect(url_for('main.edit_profile'))
            
            # Faz o hash e atualiza a senha no objeto current_user
            current_user.password = generate_password_hash(new_password, method="pbkdf2:sha256")

        old_username = current_user.username

        # ATUALIZA USERNAME E EMAIL
        current_user.username = username
        current_user.email = email

        for room in rooms.values():
            if old_username in room.members: #SE NOME ANTIGO TÁ NA LISTA DE MEMBROS
                room.members.remove(old_username) # Remove o nome antigo
                room.members.append(username)     # Adiciona o novo
            
            if room.creator == old_username: # SE ELE FOR CRIADOR DE ALGUM FORUM
                room.creator = username # ATUALIZA NOME

            for p in room.participantes: # ATUALIZA NOME NA LISTA DE PARTICIPANTES DE FÓRUM
                if p.get('id') == current_user.id:
                    p['username'] = username
        
        flash("Perfil atualizado com sucesso!", "success")
        
        return redirect(url_for('main.perfil')) # REDIRECIONA PARA TELA DE PERFIL

    return render_template("edit_profile.html")

# ROTA DE EXCLUSÃO DE CONTA
@main_bp.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    user_id = current_user.id
    username = current_user.username

    for room in rooms.values():
        # REMOVE DA LISTA DE MEMBROS
        if username in room.members:
            room.remove_member(username)

        # ATUALIZA A LISTA DE PARTICIPANTES ṔARA TODOS MENOS O USUÁRIO DELETADO
        room.participantes = [p for p in room.participantes if p['username'] != username]

    # Remover usuário do dicionário global de usuários
    if user_id in users:
        del users[user_id]
        
    # Remover da lista de online (se estiver lá)
    if username in online_users:
        online_users.discard(username)

    # 5. Logout e feedback
    logout_user()
    flash("Sua conta foi excluída permanentemente. Sentiremos sua falta!", "info")
    
    # Redireciona para a tela de login ou home
    return redirect(url_for("auth.login"))