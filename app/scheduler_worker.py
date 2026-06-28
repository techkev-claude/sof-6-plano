"""Standalone scheduler process — run alongside gunicorn to avoid double-execution."""
import time

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler

from app import create_app

log = structlog.get_logger()


def run():
    app = create_app()
    sched = BlockingScheduler()

    @sched.scheduled_job("interval", hours=1, id="check_notifications")
    def check_notifications():
        with app.app_context():
            _process_pending_notifications()

    @sched.scheduled_job("cron", hour=7, minute=0, id="daily_weather")
    def daily_weather():
        with app.app_context():
            _send_weather_alerts()

    log.info("scheduler_starting")
    sched.start()


def _process_pending_notifications():
    from datetime import datetime, timezone

    from app.extensions import db
    from app.models import Notification

    with db.session.begin():
        pending = Notification.query.filter(
            Notification.sent_at.is_(None),
            Notification.scheduled_for <= datetime.now(timezone.utc).replace(tzinfo=None),
        ).all()
        for n in pending:
            try:
                _deliver_notification(n)
                n.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
            except Exception as e:
                log.error("notification_delivery_failed", notification_id=n.id, error=str(e))


def _deliver_notification(notification):
    log.info("notification_deliver", id=notification.id, channel=notification.delivery_channel)


def _send_weather_alerts():
    log.info("weather_alerts_check")


if __name__ == "__main__":
    run()
