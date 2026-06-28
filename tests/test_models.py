import datetime

import pytest

from app.models import (
    Accommodation,
    AuditLog,
    Expense,
    FavoritePlace,
    PackingList,
    PackingListTemplate,
    Photo,
    PlanVersion,
    TimeBlock,
    Ticket,
    Trip,
    TripLeg,
    TripMember,
    User,
    AppConfig,
    AIUsage,
    TileCache,
    Notification,
)


def test_user_model(app, db):
    with app.app_context():
        u = User(username="modeluser", email="model@test.de")
        u.set_password("secret123")
        db.session.add(u)
        db.session.commit()

        loaded = User.query.filter_by(username="modeluser").first()
        assert loaded is not None
        assert loaded.check_password("secret123")
        assert not loaded.check_password("wrong")
        assert loaded.is_active
        assert not loaded.is_admin

        db.session.delete(loaded)
        db.session.commit()


def test_user_password_hash_not_plaintext(app, db):
    with app.app_context():
        u = User(username="hashtest", email="hash@test.de")
        u.set_password("mysecret")
        assert "mysecret" not in u.password_hash
        assert len(u.password_hash) > 20


def test_trip_model(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id,
            title="Testurlaub",
            start_date=datetime.date(2025, 7, 1),
            end_date=datetime.date(2025, 7, 10),
            currency="EUR",
        )
        trip.generate_share_token()
        db.session.add(trip)
        db.session.commit()

        loaded = Trip.query.filter_by(title="Testurlaub").first()
        assert loaded is not None
        assert loaded.share_token is not None
        assert len(loaded.share_token) > 10

        db.session.delete(loaded)
        db.session.commit()


def test_trip_leg_model(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id,
            title="LegTest",
            start_date=datetime.date(2025, 8, 1),
            end_date=datetime.date(2025, 8, 5),
        )
        db.session.add(trip)
        db.session.flush()

        leg = TripLeg(
            trip_id=trip.id,
            title="Wien",
            start_date=datetime.date(2025, 8, 1),
            end_date=datetime.date(2025, 8, 3),
            order_index=0,
        )
        db.session.add(leg)
        db.session.flush()

        block = TimeBlock(
            leg_id=leg.id,
            title="Museumsbesuch",
            block_type="sightseeing",
            start_datetime=datetime.datetime(2025, 8, 2, 10, 0),
            duration_minutes=90,
        )
        db.session.add(block)
        db.session.commit()

        assert block.end_datetime == datetime.datetime(2025, 8, 2, 11, 30)
        d = block.to_dict()
        assert d["title"] == "Museumsbesuch"
        assert d["duration_minutes"] == 90

        db.session.delete(trip)
        db.session.commit()


def test_plan_version_snapshot_compression(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id,
            title="VersionTest",
            start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2025, 9, 5),
        )
        db.session.add(trip)
        db.session.flush()

        v = PlanVersion(
            trip_id=trip.id,
            created_by_id=user.id,
            version_string="1.0.0",
            is_major=True,
        )
        data = {"title": "VersionTest", "legs": []}
        v.set_snapshot(data)
        db.session.add(v)
        db.session.commit()

        loaded = PlanVersion.query.filter_by(trip_id=trip.id).first()
        assert loaded.get_snapshot() == data
        assert loaded.snapshot_data_gz is not None

        db.session.delete(trip)
        db.session.commit()


def test_app_config_get_set(app, db):
    with app.app_context():
        AppConfig.set("test_key", "test_value")
        assert AppConfig.get("test_key") == "test_value"
        assert AppConfig.get("nonexistent", "default") == "default"


def test_time_block_to_dict(app, db, admin_user):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id, title="DictTest",
            start_date=datetime.date(2025, 10, 1),
            end_date=datetime.date(2025, 10, 3),
        )
        db.session.add(trip)
        db.session.flush()
        leg = TripLeg(trip_id=trip.id, title="Leg", start_date=trip.start_date, end_date=trip.end_date)
        db.session.add(leg)
        db.session.flush()
        block = TimeBlock(
            leg_id=leg.id, title="Dinner", block_type="food",
            start_datetime=datetime.datetime(2025, 10, 1, 19, 0),
            duration_minutes=60,
        )
        db.session.add(block)
        db.session.commit()

        d = block.to_dict()
        assert d["block_type"] == "food"
        assert "start_datetime" in d

        db.session.delete(trip)
        db.session.commit()


def test_all_model_classes_importable():
    models = [
        User, AppConfig, Trip, TripMember, TripLeg, Accommodation,
        TimeBlock, Ticket, Photo, Expense, PackingListTemplate,
        PackingList, PlanVersion, Notification, FavoritePlace,
        AuditLog, AIUsage, TileCache,
    ]
    assert len(models) == 18
