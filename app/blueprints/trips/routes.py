import secrets
from datetime import timedelta

import structlog
from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.trips import trips_bp
from app.blueprints.trips.forms import AddMemberForm, TripForm, TripLegForm
from app.extensions import db
from app.models import AuditLog, PlanVersion, Trip, TripLeg, TripMember, User
from app.services.versioning_service import create_major_version

log = structlog.get_logger()


def _get_trip_or_403(trip_id: int, min_permission: str = "viewer") -> Trip:
    trip = db.session.get(Trip, trip_id)
    if not trip:
        abort(404)
    if trip.owner_id == current_user.id:
        return trip
    membership = TripMember.query.filter_by(trip_id=trip_id, user_id=current_user.id).first()
    if not membership:
        abort(403)
    perms = {"viewer": 0, "editor": 1, "owner": 2}
    if perms.get(membership.permission, 0) < perms.get(min_permission, 0):
        abort(403)
    return trip


@trips_bp.route("/")
@login_required
def list_trips():
    owned = Trip.query.filter_by(owner_id=current_user.id, is_archived=False).order_by(
        Trip.start_date.asc()
    )
    memberships = (
        TripMember.query.filter_by(user_id=current_user.id)
        .join(Trip)
        .filter(Trip.is_archived == False)  # noqa: E712
        .all()
    )
    shared = [m.trip for m in memberships if m.trip.owner_id != current_user.id]
    return render_template("trips/list.html", owned_trips=owned, shared_trips=shared)


@trips_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_trip():
    form = TripForm()
    if form.validate_on_submit():
        trip = Trip(
            owner_id=current_user.id,
            title=form.title.data,
            destination=form.destination.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            currency=form.currency.data,
            budget_total=form.budget_total.data,
        )
        trip.generate_share_token()
        db.session.add(trip)
        db.session.flush()
        create_major_version(trip.id, current_user.id, "Initiale Version")
        db.session.commit()
        flash("Reise erstellt!", "success")
        return redirect(url_for("trips.trip_detail", trip_id=trip.id))
    return render_template("trips/create.html", form=form)


@trips_bp.route("/<int:trip_id>")
@login_required
def trip_detail(trip_id: int):
    trip = _get_trip_or_403(trip_id)
    membership = TripMember.query.filter_by(trip_id=trip_id, user_id=current_user.id).first()
    permission = "owner" if trip.owner_id == current_user.id else (membership.permission if membership else "viewer")
    return render_template("trips/detail.html", trip=trip, permission=permission)


@trips_bp.route("/<int:trip_id>/edit", methods=["GET", "POST"])
@login_required
def edit_trip(trip_id: int):
    trip = _get_trip_or_403(trip_id, "editor")
    form = TripForm(obj=trip)
    if form.validate_on_submit():
        form.populate_obj(trip)
        db.session.commit()
        flash("Reise aktualisiert.", "success")
        return redirect(url_for("trips.trip_detail", trip_id=trip.id))
    return render_template("trips/create.html", form=form, trip=trip)


@trips_bp.route("/<int:trip_id>/delete", methods=["POST"])
@login_required
def delete_trip(trip_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip or trip.owner_id != current_user.id:
        abort(403)
    db.session.delete(trip)
    db.session.commit()
    flash("Reise gelöscht.", "info")
    return redirect(url_for("trips.list_trips"))


@trips_bp.route("/<int:trip_id>/duplicate", methods=["POST"])
@login_required
def duplicate_trip(trip_id: int):
    original = _get_trip_or_403(trip_id)
    delta = (original.end_date - original.start_date).days

    new_trip = Trip(
        owner_id=current_user.id,
        title=f"{original.title} (Kopie)",
        destination=original.destination,
        description=original.description,
        start_date=original.start_date,
        end_date=original.end_date,
        currency=original.currency,
        budget_total=original.budget_total,
    )
    new_trip.generate_share_token()
    db.session.add(new_trip)
    db.session.flush()

    for leg in original.legs:
        new_leg = TripLeg(
            trip_id=new_trip.id,
            title=leg.title,
            start_date=leg.start_date,
            end_date=leg.end_date,
            order_index=leg.order_index,
            transport_mode=leg.transport_mode,
            notes=leg.notes,
            color=leg.color,
        )
        db.session.add(new_leg)
        db.session.flush()

        from app.models import TimeBlock
        for block in leg.time_blocks:
            new_block = TimeBlock(
                leg_id=new_leg.id,
                title=block.title,
                block_type=block.block_type,
                start_datetime=block.start_datetime,
                duration_minutes=block.duration_minutes,
                is_fixed=block.is_fixed,
                lat=block.lat,
                lng=block.lng,
                address=block.address,
                notes=block.notes,
                estimated_cost=block.estimated_cost,
            )
            db.session.add(new_block)

    create_major_version(new_trip.id, current_user.id, f"Kopie von: {original.title}")
    db.session.commit()
    flash("Reise dupliziert!", "success")
    return redirect(url_for("trips.trip_detail", trip_id=new_trip.id))


@trips_bp.route("/<int:trip_id>/members", methods=["GET", "POST"])
@login_required
def manage_members(trip_id: int):
    trip = _get_trip_or_403(trip_id, "editor")
    if trip.owner_id != current_user.id:
        abort(403)
    form = AddMemberForm()
    if form.validate_on_submit():
        identifier = form.username_or_email.data
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        if not user:
            flash("Benutzer nicht gefunden.", "error")
        elif user.id == current_user.id:
            flash("Du bist bereits Eigentümer.", "error")
        else:
            existing = TripMember.query.filter_by(trip_id=trip_id, user_id=user.id).first()
            if existing:
                existing.permission = form.permission.data
            else:
                db.session.add(TripMember(trip_id=trip_id, user_id=user.id, permission=form.permission.data))
            db.session.commit()
            flash(f"{user.username} hinzugefügt.", "success")
    return render_template("trips/members.html", trip=trip, form=form)


@trips_bp.route("/<int:trip_id>/members/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_member(trip_id: int, user_id: int):
    trip = db.session.get(Trip, trip_id)
    if not trip or trip.owner_id != current_user.id:
        abort(403)
    TripMember.query.filter_by(trip_id=trip_id, user_id=user_id).delete()
    db.session.commit()
    flash("Mitglied entfernt.", "info")
    return redirect(url_for("trips.manage_members", trip_id=trip_id))


@trips_bp.route("/<int:trip_id>/legs/new", methods=["GET", "POST"])
@login_required
def create_leg(trip_id: int):
    trip = _get_trip_or_403(trip_id, "editor")
    form = TripLegForm()
    if form.validate_on_submit():
        last_order = db.session.query(db.func.max(TripLeg.order_index)).filter_by(trip_id=trip_id).scalar() or 0
        leg = TripLeg(
            trip_id=trip_id,
            title=form.title.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            transport_mode=form.transport_mode.data,
            notes=form.notes.data,
            color=form.color.data,
            order_index=last_order + 1,
        )
        db.session.add(leg)
        db.session.commit()
        flash("Etappe erstellt.", "success")
        return redirect(url_for("trips.trip_detail", trip_id=trip_id))
    return render_template("trips/create_leg.html", form=form, trip=trip)


@trips_bp.route("/<int:trip_id>/legs/<int:leg_id>/edit", methods=["GET", "POST"])
@login_required
def edit_leg(trip_id: int, leg_id: int):
    trip = _get_trip_or_403(trip_id, "editor")
    leg = TripLeg.query.filter_by(id=leg_id, trip_id=trip_id).first_or_404()
    form = TripLegForm(obj=leg)
    if form.validate_on_submit():
        form.populate_obj(leg)
        db.session.commit()
        flash("Etappe aktualisiert.", "success")
        return redirect(url_for("trips.trip_detail", trip_id=trip_id))
    return render_template("trips/create_leg.html", form=form, trip=trip, leg=leg)


@trips_bp.route("/<int:trip_id>/legs/<int:leg_id>/delete", methods=["POST"])
@login_required
def delete_leg(trip_id: int, leg_id: int):
    trip = _get_trip_or_403(trip_id, "editor")
    leg = TripLeg.query.filter_by(id=leg_id, trip_id=trip_id).first_or_404()
    db.session.delete(leg)
    db.session.commit()
    flash("Etappe gelöscht.", "info")
    return redirect(url_for("trips.trip_detail", trip_id=trip_id))


@trips_bp.route("/shared/<token>")
def shared_view(token: str):
    trip = Trip.query.filter_by(share_token=token).first_or_404()
    return render_template("trips/shared.html", trip=trip)
