import datetime

import pytest

from app.models import Trip, TripLeg, TripMember, User
from tests.conftest import login, logout


def test_trip_list_requires_login(app, client):
    with app.app_context():
        logout(client)
        resp = client.get("/trips/", follow_redirects=False)
        assert resp.status_code in (302, 308)


def test_create_trip(app, client, admin_user, db):
    with app.app_context():
        login(client)
        resp = client.post(
            "/trips/new",
            data={
                "title": "Testtrip",
                "destination": "Wien",
                "start_date": "2025-07-01",
                "end_date": "2025-07-05",
                "currency": "EUR",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        trip = Trip.query.filter_by(title="Testtrip").first()
        assert trip is not None
        assert trip.share_token is not None


def test_trip_detail_accessible(app, client, admin_user, db):
    with app.app_context():
        login(client)
        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id, title="DetailTest",
            start_date=datetime.date(2025, 8, 1),
            end_date=datetime.date(2025, 8, 5),
        )
        trip.generate_share_token()
        db.session.add(trip)
        db.session.commit()

        resp = client.get(f"/trips/{trip.id}")
        assert resp.status_code == 200


def test_shared_link_no_login_required(app, client, admin_user, db):
    with app.app_context():
        logout(client)
        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id, title="SharedTest",
            start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2025, 9, 3),
        )
        trip.generate_share_token()
        db.session.add(trip)
        db.session.commit()

        resp = client.get(f"/trips/shared/{trip.share_token}")
        assert resp.status_code == 200
        assert b"Nur-Lese" in resp.data or b"SharedTest" in resp.data


def test_viewer_cannot_delete_trip(app, client, admin_user, db):
    with app.app_context():
        owner = User.query.filter_by(username="testadmin").first()
        viewer = User(username="vieweruser", email="viewer@test.de")
        viewer.set_password("pass123")
        db.session.add(viewer)
        db.session.flush()

        trip = Trip(
            owner_id=owner.id, title="ViewerTest",
            start_date=datetime.date(2025, 10, 1),
            end_date=datetime.date(2025, 10, 3),
        )
        db.session.add(trip)
        db.session.flush()

        membership = TripMember(trip_id=trip.id, user_id=viewer.id, permission="viewer")
        db.session.add(membership)
        db.session.commit()

        logout(client)
        client.post("/auth/login", data={"username": "vieweruser", "password": "pass123"})

        resp = client.post(f"/trips/{trip.id}/delete")
        assert resp.status_code in (403, 302)

        db.session.delete(trip)
        db.session.delete(viewer)
        db.session.commit()


def test_versioning_service_creates_major(app, db, admin_user):
    with app.app_context():
        from app.services.versioning_service import create_major_version
        from app.models import PlanVersion

        user = User.query.filter_by(username="testadmin").first()
        trip = Trip(
            owner_id=user.id, title="VersionTrip",
            start_date=datetime.date(2025, 11, 1),
            end_date=datetime.date(2025, 11, 5),
        )
        db.session.add(trip)
        db.session.flush()

        v = create_major_version(trip.id, user.id, "Init")
        db.session.commit()

        assert v.is_major
        assert v.version_string == "1.0.0"
        snapshot = v.get_snapshot()
        assert snapshot["title"] == "VersionTrip"

        db.session.delete(trip)
        db.session.commit()
