from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user

from application.extensions import rooms, generate_unique_code
from application.models.forum import Forum
from application.websockets.handlers import register_socketio_handlers
from datetime import datetime


chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/forum/<forum_id>")
@login_required
def access_forum(forum_id):
    forum = rooms.get(forum_id)

    #SE NÃO CONSEGUE FORUNS, RETORNA HOME
    if not forum:
        return (redirect(url_for("chat.home")))
    
    #forum.add_participant(current_user)

    session["room"] = forum_id
    session["name"] = current_user.username

    return redirect(url_for("chat.room"))
    #return render_template("room.html", room=forum_id, name=current_user.username, forum=forum)

@chat_bp.route("/room")
@login_required
def room():
    room = session.get("room")
    name = session.get("name")
    
    if room is None or name is None or room not in rooms:
        return redirect(url_for("main.home"))

    return render_template("room.html", room=room, username=name, messages=rooms[room].messages, participantes=rooms[room].participantes)

@chat_bp.route("/send/<room>", methods=["POST"])
@login_required
def send_message(room):

    if room not in rooms:
        return redirect(url_for("main.home"))

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
