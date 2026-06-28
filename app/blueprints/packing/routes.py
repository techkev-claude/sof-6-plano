from flask import render_template, abort
from flask_login import current_user, login_required
from app.blueprints.packing import packing_bp
from app.extensions import db
from app.models import Trip, TripMember, PackingList


@packing_bp.route("/<int:trip_id>/packing")
@login_required
def packing_list(trip_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    lists = PackingList.query.filter_by(trip_id=trip_id).all()
    return render_template("packing/list.html", trip=trip, packing_lists=lists)
