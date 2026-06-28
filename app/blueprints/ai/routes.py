from flask import render_template, abort
from flask_login import current_user, login_required
from app.blueprints.ai import ai_bp
from app.extensions import db
from app.models import Trip, TripMember, AppConfig


@ai_bp.route("/trips/<int:trip_id>/ai")
@login_required
def workspace(trip_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    if trip.owner_id != current_user.id:
        m = TripMember.query.filter_by(trip_id=trip_id, user_id=current_user.id).first()
        if not m:
            abort(403)
    ai_enabled = bool(AppConfig.get("anthropic_api_key") or AppConfig.get("openai_api_key"))
    return render_template("ai/workspace.html", trip=trip, ai_enabled=ai_enabled)
