from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user

from application.extensions import rooms, generate_unique_code
from application.models.forum import Forum
from application.websockets.handlers import register_socketio_handlers
from datetime import datetime

#BLUEPRINT DE CHAT
chat_bp = Blueprint('chat', __name__)

# ==========================
#   ROTA FORUM    
# ==========================

# ROTA PARA SABER QUAL SALA ACESSA
@chat_bp.route("/forum/<forum_id>")
@login_required #AUTENTICAÇÃO NECESSÁRIA
def access_forum(forum_id):
    forum = rooms.get(forum_id)

    #SE NÃO CONSEGUE FORUNS, RETORNA HOME
    if not forum:
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
    room = session.get("room")
    name = session.get("name")
    
    # SE NÃO TIVER NENHUM DOS VALORES, RETORNA PARA HOME
    if room is None or name is None or room not in rooms:
        return redirect(url_for("main.home"))

    #CARREGA PAGINA DO FÓRUM, MANDANDO O FORUM DA SESSÃO, NOME DO USUÁRIO, LISTA DE MENSAGENS E LISTA DE PARTICIPANTES
    return render_template("room.html", room=room, username=name, messages=rooms[room].messages, participantes=rooms[room].participantes)

#ROTA PARA MANDAR MENSAGEM
@chat_bp.route("/send/<room>", methods=["POST"])
@login_required
def send_message(room):
    #VERIFICAÇÃO DE SALA POR SEGURANÇA
    if room not in rooms:
        return redirect(url_for("main.home"))

    #ARMAZENA VALOR DA MENSAGEM
    message = request.form.get("message")

    
    if message.strip() == "":
        return redirect(url_for("chat.room"))

    # Salva a mensagem no objeto da sala
    rooms[room].messages.append({
        "user": current_user.username,
        "text": message,
        "time": datetime.now().strftime("%H:%M")
    })

    # Redireciona de volta ao chat
    return redirect(url_for("chat.room"))
