from flask import render_template, abort
from flask_login import current_user, login_required
from app.blueprints.tickets import tickets_bp
from app.extensions import db
from app.models import Trip, TripMember, Ticket


@tickets_bp.route("/<int:trip_id>/tickets")
@login_required
def vault(trip_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    tickets = Ticket.query.filter_by(trip_id=trip_id).order_by(Ticket.travel_date).all()
    return render_template("tickets/vault.html", trip=trip, tickets=tickets)
