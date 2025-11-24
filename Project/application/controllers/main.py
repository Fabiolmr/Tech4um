from flask import Blueprint, render_template
from application.models.forum import get_all_forums

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    # Busca a lista de fóruns do Model
    rooms = get_all_forums()
    # Renderiza a home passando a lista (você precisará ajustar o home.html depois)
    return render_template("home.html", rooms=rooms)