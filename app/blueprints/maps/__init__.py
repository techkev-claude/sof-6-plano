from flask import Blueprint
maps_bp = Blueprint("maps", __name__, url_prefix="/trips", template_folder="templates")
from app.blueprints.maps import routes  # noqa: E402, F401
