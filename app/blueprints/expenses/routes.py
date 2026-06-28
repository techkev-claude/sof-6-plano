from flask import render_template, abort
from flask_login import current_user, login_required
from app.blueprints.expenses import expenses_bp
from app.extensions import db
from app.models import Trip, TripMember, Expense


@expenses_bp.route("/<int:trip_id>/expenses")
@login_required
def dashboard(trip_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    expenses = Expense.query.filter_by(trip_id=trip_id).order_by(Expense.expense_date).all()
    total_spent = sum(float(e.amount_eur or e.amount) for e in expenses)
    return render_template("expenses/dashboard.html", trip=trip, expenses=expenses, total_spent=total_spent)
