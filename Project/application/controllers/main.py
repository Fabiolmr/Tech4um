from flask import Blueprint, render_template
from application.extensions import rooms

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    # Renderiza a home passando a lista (você precisará ajustar o home.html depois)
    return render_template("home.html", rooms=rooms.values())