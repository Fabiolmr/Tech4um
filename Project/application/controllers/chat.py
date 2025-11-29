from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user

from application.extensions import db
from application.models.forum import Forum
from application.models.message import Message

#BLUEPRINT DE CHAT
chat_bp = Blueprint('chat', __name__)

# ==========================
#   ROTA FORUM    
# ==========================

# ROTA PARA SABER QUAL SALA ACESSA
@chat_bp.route("/forum/<forum_id>")
@login_required #AUTENTICAÇÃO NECESSÁRIA
def access_forum(forum_id):
    forum = Forum.query.get(forum_id)

    #SE NÃO CONSEGUE FORUNS, RETORNA HOME
    if not forum:
        flash("Sala não encontrada.", "danger")
        return (redirect(url_for("chat.home")))

    session["room"] = forum_id #MUDA SALA DA SESSÃO PARA SALA ESCOLHIDA
    session["name"] = current_user.username 

    # REDIRECIONA PARA FORUM ESCOLHIDO
    return redirect(url_for("chat.room"))

#ROTA DE SALA
@chat_bp.route("/room")
@login_required
def room():
    # PEGA FORUM DA SESSÃO ATUAL
    room_id = session.get("room")
    
    # SE NÃO TIVER NENHUM DOS VALORES, RETORNA PARA HOME
    if room_id is None:
        return redirect(url_for("main.home"))

    forum = Forum.query.get(room_id)

    if not forum:
        flash("Essa sala não existe mais.", "warning")
        return redirect(url_for("main.home"))


    lista_mensagens = []
    for msg in forum.messages: # O SQLAlchemy pega todas as mensagens graças ao relationship
        lista_mensagens.append({
            "user": msg.sender.username if msg.sender else "Sistema",
            "text": msg.text,
            "time": msg.timestamp
        })

    lista_participantes = []
    for member in forum.members:
        lista_participantes.append({
            "username": member.username,
            "is_creator": (member.username == forum.creator),
            "is_member": True,
            "online": False # O status online vem do WebSocket, aqui deixamos False por enquanto
        })

    #CARREGA PAGINA DO FÓRUM, MANDANDO O FORUM DA SESSÃO, NOME DO USUÁRIO, LISTA DE MENSAGENS E LISTA DE PARTICIPANTES
    return render_template("room.html", room=forum.id, username=current_user.username, messages=lista_mensagens, participantes=lista_participantes)

#ROTA PARA MANDAR MENSAGEM
@chat_bp.route("/send/<room>", methods=["POST"])
@login_required
def send_message(room):
    #VERIFICAÇÃO DE SALA POR SEGURANÇA
    forum = Forum.query.get(room)
    if not forum:
        return redirect(url_for("main.home"))

    #ARMAZENA VALOR DA MENSAGEM
    text = request.form.get("message")
    if not text or text.strip() == "":
        return redirect(url_for("chat.room"))

    # Salva a mensagem no objeto da sala
    new_message = Message(
        text=text,
        user_id=current_user.id, # Salva o ID do usuário
        forum_id=room
    )

    db.session.add(new_message)
    db.session.commit()

    # Redireciona de volta ao chat
    return redirect(url_for("chat.room"))
