from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import login_required, current_user
from application.extensions import rooms, generate_unique_code # Importa o sistema de salas

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/forum/<int:forum_id>")
@login_required
def access_forum(forum_id):
    # Aqui você validaria se o fórum existe usando o Model
    session["room"] = forum_id
    session["name"] = current_user.username
    return render_template("room.html", room=forum_id, name=current_user.username)

@chat_bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join")
        create = request.form.get("create")

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        # Criar sala
        if create:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
            

        # Entrar em sala existente
        elif join:
            if not code:
                return render_template("home.html", error="Please enter a room code", name=name)

            if code not in rooms:
                return render_template("home.html", error="Room does not exist.", name=name)

            room = code

        session["room"] = room
        session["name"] = name

        return redirect(url_for("chat.room"))

    return render_template("home.html")


@chat_bp.route("/room")
@login_required
def room():
    room = session.get("room")
    name = session.get("name")

    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", room=room, name=name)

