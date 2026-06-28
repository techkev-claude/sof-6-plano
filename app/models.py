import gzip
import json
import secrets
from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import event

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    timezone = db.Column(db.String(64), default="UTC")
    locale = db.Column(db.String(8), default="de")
    push_subscription = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    last_login = db.Column(db.DateTime)

    trips = db.relationship("Trip", back_populates="owner", lazy="dynamic")
    trip_memberships = db.relationship("TripMember", back_populates="user", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")
    ai_usage = db.relationship("AIUsage", back_populates="user", lazy="dynamic")
    audit_logs = db.relationship("AuditLog", back_populates="user", lazy="dynamic")
    favorite_places = db.relationship("FavoritePlace", back_populates="user", lazy="dynamic")

    def set_password(self, password: str):
        import bcrypt

        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password: str) -> bool:
        import bcrypt

        return bcrypt.checkpw(password.encode(), self.password_hash.encode())


class AppConfig(db.Model):
    __tablename__ = "app_config"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    @classmethod
    def get(cls, key: str, default=None):
        row = cls.query.filter_by(key=key).first()
        return row.value if row else default

    @classmethod
    def set(cls, key: str, value: str):
        row = cls.query.filter_by(key=key).first()
        if row:
            row.value = value
            row.updated_at = utcnow()
        else:
            row = cls(key=key, value=value)
            db.session.add(row)
        db.session.commit()

    @classmethod
    def get_all(cls) -> dict:
        return {r.key: r.value for r in cls.query.all()}


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    destination = db.Column(db.String(200))
    cover_image_url = db.Column(db.String(500))
    currency = db.Column(db.String(3), default="EUR")
    budget_total = db.Column(db.Numeric(12, 2))
    share_token = db.Column(db.String(64), unique=True, index=True)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    owner = db.relationship("User", back_populates="trips")
    members = db.relationship("TripMember", back_populates="trip", cascade="all, delete-orphan")
    legs = db.relationship(
        "TripLeg", back_populates="trip", cascade="all, delete-orphan", order_by="TripLeg.order_index"
    )
    tickets = db.relationship("Ticket", back_populates="trip", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    packing_lists = db.relationship("PackingList", back_populates="trip", cascade="all, delete-orphan")
    versions = db.relationship(
        "PlanVersion", back_populates="trip", cascade="all, delete-orphan", order_by="PlanVersion.id"
    )
    notifications = db.relationship("Notification", back_populates="trip", cascade="all, delete-orphan")
    favorite_places = db.relationship("FavoritePlace", back_populates="trip", cascade="all, delete-orphan")
    photos = db.relationship("Photo", back_populates="trip", cascade="all, delete-orphan")

    def generate_share_token(self):
        self.share_token = secrets.token_urlsafe(32)

    def to_snapshot_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "destination": self.destination,
            "currency": self.currency,
            "budget_total": float(self.budget_total) if self.budget_total else None,
            "legs": [leg.to_dict() for leg in self.legs],
        }


class TripMember(db.Model):
    __tablename__ = "trip_members"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    permission = db.Column(db.String(16), nullable=False, default="viewer")  # owner, editor, viewer

    trip = db.relationship("Trip", back_populates="members")
    user = db.relationship("User", back_populates="trip_memberships")

    __table_args__ = (db.UniqueConstraint("trip_id", "user_id"),)


class TripLeg(db.Model):
    __tablename__ = "trip_legs"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    transport_mode = db.Column(db.String(32))
    notes = db.Column(db.Text)
    color = db.Column(db.String(7), default="#6366f1")

    trip = db.relationship("Trip", back_populates="legs")
    accommodations = db.relationship(
        "Accommodation", back_populates="leg", cascade="all, delete-orphan"
    )
    time_blocks = db.relationship(
        "TimeBlock",
        back_populates="leg",
        cascade="all, delete-orphan",
        order_by="TimeBlock.start_datetime",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "order_index": self.order_index,
            "transport_mode": self.transport_mode,
            "color": self.color,
            "time_blocks": [b.to_dict() for b in self.time_blocks],
        }


class Accommodation(db.Model):
    __tablename__ = "accommodations"

    id = db.Column(db.Integer, primary_key=True)
    leg_id = db.Column(db.Integer, db.ForeignKey("trip_legs.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    confirmation_number = db.Column(db.String(100))
    price_per_night = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    booking_url = db.Column(db.String(500))

    leg = db.relationship("TripLeg", back_populates="accommodations")


class TimeBlock(db.Model):
    __tablename__ = "time_blocks"

    id = db.Column(db.Integer, primary_key=True)
    leg_id = db.Column(db.Integer, db.ForeignKey("trip_legs.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    block_type = db.Column(
        db.String(32), nullable=False, default="other"
    )  # sightseeing, food, transport, accommodation, break, other
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    is_fixed = db.Column(db.Boolean, default=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    estimated_cost = db.Column(db.Numeric(10, 2))
    ai_generated = db.Column(db.Boolean, default=False)
    travel_time_to_next = db.Column(db.Integer)
    order_index = db.Column(db.Integer, default=0)

    leg = db.relationship("TripLeg", back_populates="time_blocks")

    @property
    def end_datetime(self):
        from datetime import timedelta

        return self.start_datetime + timedelta(minutes=self.duration_minutes)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "leg_id": self.leg_id,
            "title": self.title,
            "block_type": self.block_type,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "duration_minutes": self.duration_minutes,
            "is_fixed": self.is_fixed,
            "lat": self.lat,
            "lng": self.lng,
            "address": self.address,
            "notes": self.notes,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost else None,
        }


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    ticket_type = db.Column(db.String(32))  # flight, train, hotel, event, other
    encrypted_file_path = db.Column(db.String(500))
    file_uuid = db.Column(db.String(36), unique=True)
    original_filename = db.Column(db.String(255))
    file_mimetype = db.Column(db.String(100))
    ocr_data = db.Column(db.JSON)
    travel_date = db.Column(db.DateTime, index=True)
    decryption_failed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    trip = db.relationship("Trip", back_populates="tickets")


class Photo(db.Model):
    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    time_block_id = db.Column(db.Integer, db.ForeignKey("time_blocks.id"), index=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_uuid = db.Column(db.String(36), unique=True)
    original_filename = db.Column(db.String(255))
    taken_at = db.Column(db.DateTime, index=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    trip = db.relationship("Trip", back_populates="photos")
    time_block = db.relationship("TimeBlock")


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    paid_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="EUR")
    amount_eur = db.Column(db.Numeric(12, 2))
    exchange_rate = db.Column(db.Float)
    exchange_rate_date = db.Column(db.Date)
    category = db.Column(db.String(64))  # accommodation, food, transport, activity, other
    expense_date = db.Column(db.Date)
    split_type = db.Column(db.String(16), default="equal")  # equal, custom, none
    split_data = db.Column(db.JSON)
    receipt_path = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    trip = db.relationship("Trip", back_populates="expenses")
    paid_by = db.relationship("User")


class PackingListTemplate(db.Model):
    __tablename__ = "packing_list_templates"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    trip_type = db.Column(db.String(64))
    items = db.Column(db.JSON)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    owner = db.relationship("User")


class PackingList(db.Model):
    __tablename__ = "packing_lists"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, default="Packliste")
    items = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    trip = db.relationship("Trip", back_populates="packing_lists")


class PlanVersion(db.Model):
    __tablename__ = "plan_versions"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    version_string = db.Column(db.String(32), nullable=False)
    is_major = db.Column(db.Boolean, nullable=False, default=True)
    parent_major_id = db.Column(db.Integer, db.ForeignKey("plan_versions.id"))
    commit_message = db.Column(db.String(500))
    snapshot_data_gz = db.Column(db.LargeBinary)
    patch_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    trip = db.relationship("Trip", back_populates="versions")
    created_by = db.relationship("User")
    sub_versions = db.relationship("PlanVersion", foreign_keys=[parent_major_id])

    def set_snapshot(self, data: dict):
        raw = json.dumps(data).encode()
        self.snapshot_data_gz = gzip.compress(raw)

    def get_snapshot(self) -> dict | None:
        if not self.snapshot_data_gz:
            return None
        return json.loads(gzip.decompress(self.snapshot_data_gz))


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), index=True)
    notification_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    scheduled_for = db.Column(db.DateTime, index=True)
    sent_at = db.Column(db.DateTime)
    is_read = db.Column(db.Boolean, default=False)
    delivery_channel = db.Column(db.String(16), default="web")  # web, email, push

    user = db.relationship("User", back_populates="notifications")
    trip = db.relationship("Trip", back_populates="notifications")


class FavoritePlace(db.Model):
    __tablename__ = "favorite_places"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), index=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    category = db.Column(db.String(64))
    notes = db.Column(db.Text)
    visited = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship("User", back_populates="favorite_places")
    trip = db.relationship("Trip", back_populates="favorite_places")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(64))
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    extra_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    user = db.relationship("User", back_populates="audit_logs")


class AIUsage(db.Model):
    __tablename__ = "ai_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), index=True)
    provider = db.Column(db.String(32), nullable=False)
    model = db.Column(db.String(64))
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Numeric(10, 6))
    feature = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    user = db.relationship("User", back_populates="ai_usage")


class TileCache(db.Model):
    __tablename__ = "tile_cache"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), index=True)
    z = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    data = db.Column(db.LargeBinary)
    content_type = db.Column(db.String(64), default="image/png")
    cached_at = db.Column(db.DateTime, default=utcnow)

    __table_args__ = (db.UniqueConstraint("z", "x", "y"),)
