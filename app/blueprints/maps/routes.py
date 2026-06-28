from flask import render_template, abort
from flask_login import current_user, login_required
from app.blueprints.maps import maps_bp
from app.extensions import db
from app.models import Trip, TripMember


@maps_bp.route("/<int:trip_id>/map")
@login_required
def map_view(trip_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    return render_template("maps/view.html", trip=trip)
