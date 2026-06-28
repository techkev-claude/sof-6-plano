from flask import Blueprint
packing_bp = Blueprint("packing", __name__, url_prefix="/trips", template_folder="templates")
from app.blueprints.packing import routes  # noqa: E402, F401
