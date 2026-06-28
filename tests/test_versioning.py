import datetime

import pytest

from app.models import PlanVersion, Trip, User
from app.services.versioning_service import (
    create_major_version,
    create_sub_version,
    reconstruct_version,
    _cleanup_old_sub_versions,
    SUB_VERSION_CLEANUP_AFTER_N_MAJOR,
)


def _make_trip(db, user_id, title="VersionTrip"):
    trip = Trip(
        owner_id=user_id,
        title=title,
        start_date=datetime.date(2025, 1, 1),
        end_date=datetime.date(2025, 1, 5),
    )
    db.session.add(trip)
    db.session.flush()
    return trip


def test_major_version_created(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = _make_trip(db, user.id, "MajorTest")
        v = create_major_version(trip.id, user.id, "Test")
        db.session.commit()
        assert v.is_major
        assert v.version_string == "1.0.0"
        assert v.get_snapshot() is not None


def test_sub_version_created(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = _make_trip(db, user.id, "SubTest")
        create_major_version(trip.id, user.id, "Major")
        db.session.commit()
        sub = create_sub_version(trip.id, user.id)
        db.session.commit()
        assert not sub.is_major
        assert "1.0." in sub.version_string


def test_reconstruct_major_version(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = _make_trip(db, user.id, "ReconstructTest")
        v = create_major_version(trip.id, user.id, "Reconstruct")
        db.session.commit()
        result = reconstruct_version(v.id)
        assert result is not None
        assert result["title"] == "ReconstructTest"


def test_reconstruct_sub_version(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = _make_trip(db, user.id, "ReconstructSub")
        create_major_version(trip.id, user.id)
        db.session.commit()
        sub = create_sub_version(trip.id, user.id)
        db.session.commit()
        result = reconstruct_version(sub.id)
        assert result is not None


def test_sub_version_cleanup(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = _make_trip(db, user.id, "CleanupTest")

        m1 = create_major_version(trip.id, user.id, "M1")
        db.session.commit()

        sub1 = create_sub_version(trip.id, user.id)
        sub2 = create_sub_version(trip.id, user.id)
        db.session.commit()

        m2 = create_major_version(trip.id, user.id, "M2")
        db.session.commit()

        m3 = create_major_version(trip.id, user.id, "M3")
        db.session.commit()

        remaining_subs = PlanVersion.query.filter_by(
            trip_id=trip.id, is_major=False, parent_major_id=m1.id
        ).count()
        assert remaining_subs == 0

        still_has_major = PlanVersion.query.filter_by(id=m1.id).first()
        assert still_has_major is not None
