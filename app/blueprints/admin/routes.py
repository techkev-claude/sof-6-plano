import functools

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models import AppConfig, AuditLog, User


def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated


@admin_bp.route("/")
@admin_required
def dashboard():
    user_count = User.query.count()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template("admin/dashboard.html", user_count=user_count, recent_logs=recent_logs)


@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def create_user():
    from app.blueprints.setup.forms import SetupStep1Form

    form = SetupStep1Form()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Benutzername bereits vergeben.", "error")
        else:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f"Benutzer {user.username} erstellt.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/create_user.html", form=form)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user or user.id == current_user.id:
        abort(400)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"Benutzer {'aktiviert' if user.is_active else 'deaktiviert'}.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/config", methods=["GET", "POST"])
@admin_required
def config():
    configs = AppConfig.query.order_by(AppConfig.key).all()
    if request.method == "POST":
        for c in configs:
            new_val = request.form.get(c.key)
            if new_val is not None and new_val != c.value:
                c.value = new_val
        db.session.commit()
        flash("Konfiguration gespeichert.", "success")
        return redirect(url_for("admin.config"))
    sensitive_keys = {"fernet_key", "anthropic_api_key", "openai_api_key", "smtp_password", "vapid_private_key"}
    return render_template("admin/config.html", configs=configs, sensitive_keys=sensitive_keys)
