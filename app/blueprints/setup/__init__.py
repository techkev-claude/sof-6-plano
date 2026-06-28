from flask import Blueprint
setup_bp = Blueprint("setup", __name__, url_prefix="/setup", template_folder="templates")
from app.blueprints.setup import routes  # noqa: E402, F401
