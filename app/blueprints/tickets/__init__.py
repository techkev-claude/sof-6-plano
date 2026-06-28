from flask import Blueprint
tickets_bp = Blueprint("tickets", __name__, url_prefix="/trips", template_folder="templates")
from app.blueprints.tickets import routes  # noqa: E402, F401
