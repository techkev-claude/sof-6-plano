import datetime
import json

import pytest

from app.models import TimeBlock, Trip, TripLeg, User
from tests.conftest import login


def _make_trip_with_block(db, user_id):
    trip = Trip(
        owner_id=user_id, title="PlannerTest",
        start_date=datetime.date(2025, 6, 1),
        end_date=datetime.date(2025, 6, 5),
    )
    trip.generate_share_token()
    db.session.add(trip)
    db.session.flush()

    leg = TripLeg(
        trip_id=trip.id, title="Wien",
        start_date=datetime.date(2025, 6, 1),
        end_date=datetime.date(2025, 6, 3),
    )
    db.session.add(leg)
    db.session.flush()

    block = TimeBlock(
        leg_id=leg.id, title="Museum",
        block_type="sightseeing",
        start_datetime=datetime.datetime(2025, 6, 2, 10, 0),
        duration_minutes=90,
    )
    db.session.add(block)
    db.session.commit()
    return trip, leg, block


def test_get_blocks_api(app, client, admin_user, db):
    with app.app_context():
        login(client)
        user = User.query.filter_by(username="testadmin").first()
        trip, leg, block = _make_trip_with_block(db, user.id)

        resp = client.get(f"/api/trips/{trip.id}/blocks")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == "Museum"


def test_patch_block_api(app, client, admin_user, db):
    with app.app_context():
        login(client)
        user = User.query.filter_by(username="testadmin").first()
        trip, leg, block = _make_trip_with_block(db, user.id)

        resp = client.patch(
            f"/api/blocks/{block.id}",
            data=json.dumps({"start_datetime": "2025-06-02T11:00:00"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["ok"] is True
        assert "conflicts" in data


def test_conflict_detection(app, db, admin_user):
    with app.app_context():
        from app.blueprints.api.routes import _check_conflicts

        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id, title="ConflictTest",
            start_date=datetime.date(2025, 7, 1),
            end_date=datetime.date(2025, 7, 3),
        )
        db.session.add(trip)
        db.session.flush()

        leg = TripLeg(
            trip_id=trip.id, title="Leg",
            start_date=datetime.date(2025, 7, 1),
            end_date=datetime.date(2025, 7, 3),
        )
        db.session.add(leg)
        db.session.flush()

        b1 = TimeBlock(
            leg_id=leg.id, title="Block1", block_type="other",
            start_datetime=datetime.datetime(2025, 7, 1, 10, 0),
            duration_minutes=60,
        )
        b2 = TimeBlock(
            leg_id=leg.id, title="Block2", block_type="other",
            start_datetime=datetime.datetime(2025, 7, 1, 10, 30),
            duration_minutes=60,
        )
        db.session.add_all([b1, b2])
        db.session.commit()

        conflicts = _check_conflicts(leg.id)
        assert len(conflicts) > 0
        assert any(c["block_a"] == b1.id or c["block_b"] == b1.id for c in conflicts)


def test_no_conflict_non_overlapping(app, db, admin_user):
    with app.app_context():
        from app.blueprints.api.routes import _check_conflicts

        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id, title="NoConflict",
            start_date=datetime.date(2025, 8, 1),
            end_date=datetime.date(2025, 8, 3),
        )
        db.session.add(trip)
        db.session.flush()
        leg = TripLeg(trip_id=trip.id, title="Leg", start_date=trip.start_date, end_date=trip.end_date)
        db.session.add(leg)
        db.session.flush()

        b1 = TimeBlock(
            leg_id=leg.id, title="B1", block_type="other",
            start_datetime=datetime.datetime(2025, 8, 1, 10, 0), duration_minutes=60,
        )
        b2 = TimeBlock(
            leg_id=leg.id, title="B2", block_type="other",
            start_datetime=datetime.datetime(2025, 8, 1, 11, 0), duration_minutes=60,
        )
        db.session.add_all([b1, b2])
        db.session.commit()

        conflicts = _check_conflicts(leg.id)
        assert conflicts == []
