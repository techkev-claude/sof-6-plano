"""Seed script — creates a Wien example trip for testing."""
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Trip, TripLeg, TimeBlock, User
from app.services.versioning_service import create_major_version


def seed():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            print("Kein Admin-Benutzer gefunden. Bitte Setup zuerst durchführen.")
            return

        existing = Trip.query.filter_by(title="Wien Citytrip").first()
        if existing:
            print("Beispiel-Trip existiert bereits.")
            return

        trip = Trip(
            owner_id=admin.id,
            title="Wien Citytrip",
            destination="Wien, Österreich",
            description="Ein typisches Wochenende in Wien: Museen, Kaffeehäuser und Konzerte.",
            start_date=datetime.date(2025, 10, 3),
            end_date=datetime.date(2025, 10, 5),
            currency="EUR",
            budget_total=500,
        )
        trip.generate_share_token()
        db.session.add(trip)
        db.session.flush()

        leg = TripLeg(
            trip_id=trip.id,
            title="Wien",
            start_date=datetime.date(2025, 10, 3),
            end_date=datetime.date(2025, 10, 5),
            order_index=0,
            transport_mode="transit",
            color="#6366f1",
        )
        db.session.add(leg)
        db.session.flush()

        blocks = [
            TimeBlock(
                leg_id=leg.id, title="Ankunft Wien Hauptbahnhof", block_type="transport",
                start_datetime=datetime.datetime(2025, 10, 3, 10, 0), duration_minutes=30,
                lat=48.1852, lng=16.3777,
            ),
            TimeBlock(
                leg_id=leg.id, title="Kunsthistorisches Museum", block_type="sightseeing",
                start_datetime=datetime.datetime(2025, 10, 3, 11, 0), duration_minutes=180,
                lat=48.2036, lng=16.3616, estimated_cost=21,
            ),
            TimeBlock(
                leg_id=leg.id, title="Mittagessen Naschmarkt", block_type="food",
                start_datetime=datetime.datetime(2025, 10, 3, 14, 30), duration_minutes=60,
                lat=48.1980, lng=16.3667, estimated_cost=15,
            ),
            TimeBlock(
                leg_id=leg.id, title="Stephansdom", block_type="sightseeing",
                start_datetime=datetime.datetime(2025, 10, 3, 16, 0), duration_minutes=60,
                lat=48.2083, lng=16.3730,
            ),
            TimeBlock(
                leg_id=leg.id, title="Abendessen Figlmüller", block_type="food",
                start_datetime=datetime.datetime(2025, 10, 3, 19, 0), duration_minutes=90,
                lat=48.2090, lng=16.3745, estimated_cost=35,
            ),
            TimeBlock(
                leg_id=leg.id, title="Wiener Philharmoniker Konzert", block_type="sightseeing",
                start_datetime=datetime.datetime(2025, 10, 4, 19, 30), duration_minutes=120,
                lat=48.2031, lng=16.3694, is_fixed=True, estimated_cost=80,
            ),
            TimeBlock(
                leg_id=leg.id, title="Frühstück Café Central", block_type="food",
                start_datetime=datetime.datetime(2025, 10, 5, 9, 0), duration_minutes=60,
                lat=48.2102, lng=16.3659, estimated_cost=12,
            ),
            TimeBlock(
                leg_id=leg.id, title="Abreise Wien Hauptbahnhof", block_type="transport",
                start_datetime=datetime.datetime(2025, 10, 5, 14, 0), duration_minutes=30,
                lat=48.1852, lng=16.3777,
            ),
        ]
        db.session.add_all(blocks)
        create_major_version(trip.id, admin.id, "Wien Beispiel-Trip")
        db.session.commit()

        print(f"Wien Beispiel-Trip erstellt (ID: {trip.id})")


if __name__ == "__main__":
    seed()
