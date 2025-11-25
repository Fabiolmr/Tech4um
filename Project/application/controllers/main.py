from flask import Blueprint, render_template
from flask_login import login_required
from application.extensions import rooms

main_bp = Blueprint('main', __name__)

# HOME PÚBLICA
@main_bp.route("/")
def home():
    return render_template("home.html")


