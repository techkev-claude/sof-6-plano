from flask import Blueprint
versioning_bp = Blueprint("versioning", __name__, url_prefix="/trips", template_folder="templates")
from app.blueprints.versioning import routes  # noqa: E402, F401
