from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from application.extensions import rooms, generate_unique_code
from application.models.forum import Forum

main_bp = Blueprint('main', __name__)

# HOME PÚBLICA
@main_bp.route("/", methods=["GET", "POST"])
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



