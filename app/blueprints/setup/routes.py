import base64

import structlog
from cryptography.fernet import Fernet
from flask import (
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.blueprints.setup import setup_bp
from app.blueprints.setup.forms import (
    SetupStep1Form,
    SetupStep2Form,
    SetupStep3Form,
    SetupStep4Form,
)
from app.extensions import db
from app.models import AppConfig, User

log = structlog.get_logger()

SESSION_KEY = "setup_data"


def _setup_done():
    return User.query.first() is not None


@setup_bp.route("/", methods=["GET", "POST"])
def wizard():
    if _setup_done():
        return redirect(url_for("auth.login"))

    step = request.args.get("step", "1")
    if step not in ("1", "2", "3", "4"):
        step = "1"

    forms = {
        "1": SetupStep1Form,
        "2": SetupStep2Form,
        "3": SetupStep3Form,
        "4": SetupStep4Form,
    }
    form = forms[step]()

    if form.validate_on_submit():
        data = session.get(SESSION_KEY, {})
        data[f"step{step}"] = form.data
        data[f"step{step}"].pop("csrf_token", None)
        data[f"step{step}"].pop("submit", None)
        session[SESSION_KEY] = data

        if step == "4":
            return _finalize_setup(data)

        next_step = str(int(step) + 1)
        return redirect(url_for("setup.wizard", step=next_step))

    return render_template("setup/wizard.html", form=form, step=int(step))


def _finalize_setup(data: dict) -> Response:
    step1 = data.get("step1", {})
    step2 = data.get("step2", {})
    step3 = data.get("step3", {})
    step4 = data.get("step4", {})

    fernet_key = Fernet.generate_key()
    vapid_private, vapid_public = _generate_vapid_keys()

    user = User(
        username=step1["username"],
        email=step1["email"],
        is_admin=True,
    )
    user.set_password(step1["password"])
    db.session.add(user)

    config_entries = {
        "fernet_key": fernet_key.decode(),
        "vapid_private_key": vapid_private,
        "vapid_public_key": vapid_public,
        "ai_provider": step2.get("ai_provider", "anthropic"),
        "anthropic_api_key": step2.get("anthropic_api_key", ""),
        "openai_api_key": step2.get("openai_api_key", ""),
        "owm_api_key": step2.get("owm_api_key", ""),
        "google_maps_api_key": step2.get("google_maps_api_key", ""),
        "smtp_host": step3.get("smtp_host", ""),
        "smtp_port": str(step3.get("smtp_port", 587)),
        "smtp_user": step3.get("smtp_user", ""),
        "smtp_password": step3.get("smtp_password", ""),
        "smtp_from": step3.get("smtp_from", ""),
        "smtp_tls": "true" if step3.get("smtp_tls") else "false",
        "default_timezone": step4.get("default_timezone", "UTC"),
        "default_currency": step4.get("default_currency", "EUR"),
        "default_locale": step4.get("default_locale", "de"),
        "default_transport_mode": step4.get("default_transport_mode", "transit"),
        "planner_snap_minutes": str(step4.get("planner_snap_minutes", "15")),
        "offline_map_zoom_min": str(step4.get("offline_map_zoom_min", 12)),
        "offline_map_zoom_max": str(step4.get("offline_map_zoom_max", 17)),
        "max_upload_size_mb": "50",
        "backup_enabled": "false",
        "setup_complete": "true",
    }

    for key, value in config_entries.items():
        db.session.add(AppConfig(key=key, value=value or ""))

    db.session.commit()
    log.info("setup_complete", admin_user=step1["username"])

    session.pop(SESSION_KEY, None)
    session["fernet_key_download"] = fernet_key.decode()

    return redirect(url_for("setup.download_fernet_key"))


@setup_bp.route("/fernet-key")
def download_fernet_key():
    key = session.pop("fernet_key_download", None)
    if not key:
        return redirect(url_for("auth.login"))
    return render_template("setup/fernet_key_download.html", fernet_key=key)


@setup_bp.route("/fernet-key/download")
def fernet_key_file():
    key = request.args.get("key", "")
    if not key:
        return redirect(url_for("auth.login"))
    return Response(
        key,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=plano-fernet-master.key"},
    )


def _generate_vapid_keys() -> tuple[str, str]:
    try:
        from py_vapid import Vapid

        v = Vapid()
        v.generate_keys()
        private_pem = v.private_key.private_bytes(
            encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.PEM,
            format=__import__("cryptography").hazmat.primitives.serialization.PrivateFormat.PKCS8,
            encryption_algorithm=__import__(
                "cryptography"
            ).hazmat.primitives.serialization.NoEncryption(),
        ).decode()
        public_raw = v.public_key.public_bytes(
            encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.X962,
            format=__import__(
                "cryptography"
            ).hazmat.primitives.serialization.PublicFormat.UncompressedPoint,
        )
        public_b64 = base64.urlsafe_b64encode(public_raw).rstrip(b"=").decode()
        return private_pem, public_b64
    except Exception:
        import os

        private = base64.urlsafe_b64encode(os.urandom(32)).decode()
        public = base64.urlsafe_b64encode(os.urandom(65)).decode()
        return private, public
