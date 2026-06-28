from flask import jsonify, request
from flask_login import current_user, login_required
from app.blueprints.notifications import notifications_bp
from app.extensions import db
from app.models import Notification


@notifications_bp.route("/")
@login_required
def list_notifications():
    notes = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(
        Notification.scheduled_for.desc()
    ).limit(20).all()
    return jsonify([{"id": n.id, "title": n.title, "body": n.body} for n in notes])


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id: int):
    n = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    n.is_read = True
    db.session.commit()
    return jsonify({"ok": True})
