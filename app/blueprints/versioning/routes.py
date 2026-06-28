from flask import render_template, abort, flash, redirect, url_for
from flask_login import current_user, login_required
from app.blueprints.versioning import versioning_bp
from app.extensions import db
from app.models import Trip, TripMember, PlanVersion
from app.services.versioning_service import create_major_version, reconstruct_version


@versioning_bp.route("/<int:trip_id>/versions")
@login_required
def version_timeline(trip_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    versions = PlanVersion.query.filter_by(trip_id=trip_id).order_by(PlanVersion.id.desc()).all()
    return render_template("versioning/timeline.html", trip=trip, versions=versions)


@versioning_bp.route("/<int:trip_id>/versions/<int:version_id>/restore", methods=["POST"])
@login_required
def restore_version(trip_id: int, version_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip or trip.owner_id != current_user.id:
        abort(403)
    snapshot = reconstruct_version(version_id)
    if not snapshot:
        flash("Version konnte nicht wiederhergestellt werden.", "error")
        return redirect(url_for("versioning.version_timeline", trip_id=trip_id))
    create_major_version(trip_id, current_user.id, f"Wiederhergestellt von Version {version_id}")
    db.session.commit()
    flash("Version wiederhergestellt.", "success")
    return redirect(url_for("trips.trip_detail", trip_id=trip_id))
