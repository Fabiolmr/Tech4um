from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required, logout_user
from application.extensions import generate_unique_code, socketio, db
from application.models.forum import Forum
from application.models.user import User
from application.controllers.auth import is_strong_password
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

    #AVIZA A COMUNICAÇÃO WEBSOCKET SOBRE NOVA LISTA DE USUÁRIOS ONLINE
    socketio.emit("online_users", list(online_users))

#ROTA DISCONNECT
@socketio.on("disconnect")
def handle_disconnect():
    #SE O USUÁRIO ESTÁ AUTENTICADO
    if current_user.is_authenticated:
        #RETIRA DA LISTA
        online_users.discard(current_user.username)

    #AVIZA A COMUNICAÇÃO WEBSOCKET SOBRE NOVA LISTA DE USUÁRIOS ONLINE
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
            if Forum.query.filter_by(name=create_name).first():
                flash("Nome já em uso", "danger")
                return redirect(url_for("main.home"))
            
            #NOVO CÓDIGO
            new_id = generate_unique_code(4)
            while Forum.query.get(new_id): # Se existir, gera outro
                new_id = generate_unique_code(4)
            
            # NOVO FÓRUM
            new_forum = Forum(id=new_id, name=create_name, description=create_desc, creator=current_user.username)
            #SALVA NOVO FÓRUM NA POSIÇÃO COM NOVO ID
            new_forum.members.append(current_user)
            
            try:
                db.session.add(new_forum)
                db.session.commit()


                socketio.emit("new_room", {
                    "id": new_id,
                    "name": create_name,
                    "description": create_desc,
                    "creator": current_user.username
                })

                # REDIRECIONA PARA ROTA DE ACESSAR FORUM
                flash("Fórum criado com sucesso!", "success")
                return redirect(url_for("chat.access_forum", forum_id=new_id))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash("Erro ao criar sala. Tente novamente.", "danger")

        # ------------- Entrar em fórum existente -------------
        code = request.form.get("entrar") #RECEBE AÇÃO DO BOTÃO ENTRAR
        if code:
            forum = Forum.query.get(code) # Busca no Neon
            if forum:
                return redirect(url_for("chat.access_forum", forum_id=code))
            else:
                flash("Código inválido", "danger")
    
    all_rooms = Forum.query.all()
    return render_template("home.html", rooms=all_rooms)


# ==========================
#   ROTA MEMBROS    
# ==========================

# ROTA PARA SER MEMBRO
@main_bp.route("/join_member/<forum_id>", methods=["POST"])
@login_required # INDICA QUE PRECISA ESTAR LOGADO
def join_member(forum_id):
    forum = Forum.query.get(forum_id)

    if forum:
        # ADICONA USUÁRIO ATUAL NA LISTA DE MEMBROS
        if current_user not in forum.members:
            forum.members.append(current_user) # SQLAlchemy gerencia a tabela auxiliar
            db.session.commit()
            flash(f"Agora você é membro do fórum {forum.name}!", "success")

        socketio.emit("update_member_count", {
            "forum_id": forum_id,
            "count": len(forum.members)
        })
    else:
        flash("Fórum não encontrado.", "danger")
    
    # REDIRECIONA PARA HOME
    return redirect(url_for("main.home"))

#ROTA PARA DEIXAR DE SER MEMBRO
@main_bp.route("/leave_member/<forum_id>", methods=["POST"])
@login_required #AUTENTICAÇÃO NECESSÁRIA
def leave_member(forum_id):
    forum = Forum.query.get(forum_id)

    if current_user in forum.members:
            forum.members.remove(current_user) # Remove da lista
            db.session.commit()
            
            flash(f"Você saiu do fórum {forum.name}.", "info")
            
            socketio.emit("update_member_count", {
                "forum_id": forum_id,
                "count": len(forum.members)
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
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email),
            User.id != current_user.id
        ).first()

        if existing_user:
            if existing_user.username == username:
                flash("Nome de usuário já está em uso.", "danger")
            else:
                flash("E-mail já está em uso.", "danger")
            return redirect(url_for('main.edit_profile'))

        # PROCESSAR A NOVA SENHA
        if new_password:
            if new_password != confirm_new_password:
                flash("A nova senha e a confirmação não coincidem.", "danger")
                return redirect(url_for('main.edit_profile'))
            

            if not is_strong_password(new_password):
                flash("A senha é muito fraca. Deve ter pelo menos 8 caracteres, incluir maiúsculas, minúsculas, números e pelo menos um caracter especial", "danger")
                return redirect(url_for('main.edit_profile'))
            # Faz o hash e atualiza a senha no objeto current_user
            current_user.password = generate_password_hash(new_password, method="pbkdf2:sha256")

        # ATUALIZA USERNAME E EMAIL
        current_user.username = username
        current_user.email = email

        try:
            db.session.commit() # Salva todas as alterações no Neon
            flash("Perfil atualizado com sucesso!", "success")
        except:
            db.session.rollback()
            flash("Erro ao atualizar perfil.", "danger")

        
        flash("Perfil atualizado com sucesso!", "success")
        
        return redirect(url_for('main.perfil')) # REDIRECIONA PARA TELA DE PERFIL

    return render_template("edit_profile.html")

# ROTA DE EXCLUSÃO DE CONTA
@main_bp.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    try:
        db.session.delete(current_user)
        db.session.commit()
    
        online_users.discard(current_user.username)

        logout_user()
        flash("Sua conta foi excluída permanentemente.", "info")
        return redirect(url_for("auth.login"))
    
    except Exception as e:
        db.session.rollback()
        flash("Erro ao excluir conta. Tente novamente.", "danger")
        return redirect(url_for("main.perfil"))