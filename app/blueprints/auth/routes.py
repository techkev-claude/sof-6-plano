from datetime import datetime, timezone

import structlog
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm
from app.extensions import db, limiter
from app.models import AuditLog, User

log = structlog.get_logger()


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("trips.list_trips"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
            db.session.commit()
            log.info("user_login", user_id=user.id, username=user.username)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("trips.list_trips"))
        flash("Ungültige Anmeldedaten.", "error")
        _log_failed_login(form.username.data)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log.info("user_logout", user_id=current_user.id)
    logout_user()
    flash("Du wurdest abgemeldet.", "info")
    return redirect(url_for("auth.login"))


def _log_failed_login(username: str):
    entry = AuditLog(
        action="login_failed",
        resource_type="user",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:500],
        extra_data={"username": username},
    )
    db.session.add(entry)
    db.session.commit()
