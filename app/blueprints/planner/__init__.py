from flask import Blueprint
planner_bp = Blueprint("planner", __name__, url_prefix="/trips", template_folder="templates")
from app.blueprints.planner import routes  # noqa: E402, F401
