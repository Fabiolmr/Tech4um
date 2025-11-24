from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user

from application.extensions import rooms, generate_unique_code
from application.models.forum import Forum

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/forum/<forum_id>")
@login_required
def access_forum(forum_id):
    forum = rooms.get(forum_id)

    #SE NÃO CONSEGUE FORUNS, RETORNA HOME
    if not forum:
        return (redirect(url_for("chat.home")))
    
    forum.add_participant(current_user)

    session["room"] = forum_id
    session["name"] = current_user.username

    return render_template("room.html", room=forum_id, name=current_user.username, forum=forum)


@chat_bp.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        create_name = request.form.get("create_name")
        create_desc = request.form.get("create-desc")

        #------------ sequencia para criação de forum --------------------
        if create_name:
            #VERIFICA SE USUÁRIO JÁ TÁ LOGADO
            if not current_user.is_authenticated:
                flash("Você precisa estar logado para criar uma sala.", "danger")
                return redirect(url_for("auth.login"))

            new_id = generate_unique_code(4)
            # NOVO FORUM
            new_forum = Forum(new_id, create_name, create_desc)
            rooms[new_id] = new_forum
            return redirect(url_for("chat.access_forum", forum_id=new_id))

        #------------- sequencia para entrar em forum -----------------
        code = request.form.get("entrar")
        if code in rooms: # se código está na lista de fóruns
            return redirect(url_for("chat.access_forum", forum_id=code))
        
    return render_template("home.html", rooms=rooms.values()) # rooms=rooms.values() persiste a lista de fóruns


@chat_bp.route("/room")
@login_required
def room():
    room = session.get("room")
    name = session.get("name")
    
    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", room=room, name=name)

