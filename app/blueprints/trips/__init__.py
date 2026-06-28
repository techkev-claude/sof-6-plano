from flask import Blueprint
trips_bp = Blueprint("trips", __name__, url_prefix="/trips", template_folder="templates")
from app.blueprints.trips import routes  # noqa: E402, F401
