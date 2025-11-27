from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from application.extensions import rooms, generate_unique_code, socketio
from application.models.forum import Forum

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
            new_forum = Forum(new_id, create_name, create_desc)
            rooms[new_id] = new_forum

            socketio.emit("new_room", {
                "id": new_id,
                "name": create_name,
                "description": create_desc
            })

            return redirect(url_for("chat.access_forum", forum_id=new_id))

        # ------------- Entrar em fórum existente -------------
        code = request.form.get("entrar")
        if code in rooms:
            return redirect(url_for("chat.access_forum", forum_id=code))

    return render_template("home.html", rooms=rooms.values())
