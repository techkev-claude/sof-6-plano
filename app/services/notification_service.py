import structlog
from app.extensions import db
from app.models import Notification, User

log = structlog.get_logger()


def create_notification(user_id: int, title: str, body: str, trip_id: int | None = None,
                        notification_type: str = "info", channel: str = "web") -> Notification:
    n = Notification(
        user_id=user_id,
        trip_id=trip_id,
        notification_type=notification_type,
        title=title,
        body=body,
        delivery_channel=channel,
    )
    db.session.add(n)
    return n
