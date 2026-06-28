from flask import Blueprint
expenses_bp = Blueprint("expenses", __name__, url_prefix="/trips", template_folder="templates")
from app.blueprints.expenses import routes  # noqa: E402, F401
