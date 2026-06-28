from datetime import datetime

import structlog
from flask import abort, jsonify, request
from flask_login import current_user, login_required

from app.blueprints.api import api_bp
from app.extensions import db, limiter
from app.models import AppConfig, PlanVersion, TimeBlock, Trip, TripMember
from app.services.versioning_service import create_major_version, create_sub_version

log = structlog.get_logger()


def _check_trip_permission(trip_id: int, min_permission: str = "viewer"):
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


@api_bp.route("/trips/<int:trip_id>/blocks")
@login_required
@limiter.limit("100 per minute")
def get_blocks(trip_id: int):
    _check_trip_permission(trip_id)
    trip = db.session.get(Trip, trip_id)
    blocks = []
    for leg in trip.legs:
        for block in leg.time_blocks:
            blocks.append(block.to_dict())
    return jsonify(blocks)


@api_bp.route("/blocks/<int:block_id>", methods=["PATCH"])
@login_required
@limiter.limit("100 per minute")
def update_block(block_id: int):
    block = db.session.get(TimeBlock, block_id)
    if not block:
        abort(404)
    _check_trip_permission(block.leg.trip_id, "editor")

    data = request.get_json()
    if not data:
        abort(400)

    if "start_datetime" in data:
        try:
            block.start_datetime = datetime.fromisoformat(data["start_datetime"])
        except ValueError:
            return jsonify({"error": "invalid_datetime"}), 400

    if "duration_minutes" in data:
        block.duration_minutes = int(data["duration_minutes"])

    if "title" in data:
        block.title = data["title"][:200]

    db.session.commit()

    conflicts = _check_conflicts(block.leg_id)
    return jsonify({"ok": True, "conflicts": conflicts})


@api_bp.route("/trips/<int:trip_id>/autosave", methods=["POST"])
@login_required
@limiter.limit("60 per minute")
def autosave(trip_id: int):
    _check_trip_permission(trip_id, "editor")
    version = create_sub_version(trip_id, current_user.id)
    db.session.commit()
    return jsonify({"version": version.version_string})


@api_bp.route("/trips/<int:trip_id>/save", methods=["POST"])
@login_required
def manual_save(trip_id: int):
    _check_trip_permission(trip_id, "editor")
    data = request.get_json() or {}
    message = data.get("message", "")
    version = create_major_version(trip_id, current_user.id, message)
    db.session.commit()
    return jsonify({"version": version.version_string})


@api_bp.route("/weather/<int:trip_id>")
@login_required
@limiter.limit("20 per minute")
def get_weather(trip_id: int):
    _check_trip_permission(trip_id)
    api_key = AppConfig.get("owm_api_key")
    if not api_key:
        return jsonify({"error": "no_api_key"})

    from app.services.weather_client import get_trip_weather
    try:
        result = get_trip_weather(trip_id, api_key)
        return jsonify(result)
    except Exception as e:
        log.error("weather_fetch_error", error=str(e))
        return jsonify({"error": "fetch_failed"})


@api_bp.route("/legs/reorder", methods=["POST"])
@login_required
def reorder_legs():
    from app.models import TripLeg
    data = request.get_json() or {}
    trip_id = data.get("trip_id")
    order = data.get("order", [])

    if not trip_id:
        abort(400)

    _check_trip_permission(trip_id, "editor")

    for i, leg_id in enumerate(order):
        leg = TripLeg.query.filter_by(id=leg_id, trip_id=trip_id).first()
        if leg:
            leg.order_index = i

    db.session.commit()
    return jsonify({"ok": True})


def _check_conflicts(leg_id: int) -> list:
    blocks = (
        TimeBlock.query.filter_by(leg_id=leg_id)
        .order_by(TimeBlock.start_datetime.asc())
        .all()
    )
    conflicts = []
    for i, b in enumerate(blocks):
        for j in range(i + 1, len(blocks)):
            other = blocks[j]
            if b.end_datetime > other.start_datetime:
                conflicts.append({"block_a": b.id, "block_b": other.id})
            else:
                break
    return conflicts
