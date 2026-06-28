from flask import abort, render_template
from flask_login import current_user, login_required

from app.blueprints.planner import planner_bp
from app.extensions import db
from app.models import Trip, TripMember


def _get_trip_or_403(trip_id: int) -> tuple:
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    if trip.owner_id == current_user.id:
        return trip, "owner"
    membership = TripMember.query.filter_by(trip_id=trip_id, user_id=current_user.id).first()
    if not membership:
        abort(403)
    return trip, membership.permission


@planner_bp.route("/<int:trip_id>/planner")
@login_required
def timeline(trip_id: int):
    trip, permission = _get_trip_or_403(trip_id)
    return render_template("planner/timeline.html", trip=trip, permission=permission)


@planner_bp.route("/<int:trip_id>/calendar")
@login_required
def calendar(trip_id: int):
    trip, permission = _get_trip_or_403(trip_id)
    return render_template("planner/calendar.html", trip=trip, permission=permission)
