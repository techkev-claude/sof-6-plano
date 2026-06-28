import os

import structlog
from flask import Flask, redirect, url_for

from app.config import Config
from app.extensions import babel, csrf, db, limiter, login_manager

log = structlog.get_logger()


def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=False)

    if config_class is None:
        config_class = Config
    app.config.from_object(config_class)

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_shell_context(app)
    _init_db(app)

    return app


def _init_extensions(app: Flask):
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Bitte melde dich an."
    login_manager.login_message_category = "info"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask):
    from app.blueprints.auth import auth_bp
    from app.blueprints.setup import setup_bp
    from app.blueprints.trips import trips_bp
    from app.blueprints.planner import planner_bp
    from app.blueprints.ai import ai_bp
    from app.blueprints.packing import packing_bp
    from app.blueprints.tickets import tickets_bp
    from app.blueprints.expenses import expenses_bp
    from app.blueprints.maps import maps_bp
    from app.blueprints.notifications import notifications_bp
    from app.blueprints.versioning import versioning_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(packing_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(maps_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(versioning_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        from flask_login import current_user

        if current_user.is_authenticated:
            return redirect(url_for("trips.list_trips"))
        return redirect(url_for("auth.login"))

    @app.route("/health")
    def health():
        from flask import jsonify

        return jsonify({"status": "ok"})


def _register_error_handlers(app: Flask):
    from flask import render_template

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        log.error("server_error", error=str(e))
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template

        return render_template("errors/403.html"), 403

    @app.errorhandler(429)
    def too_many_requests(e):
        from flask import render_template

        return render_template("errors/429.html"), 429


def _register_shell_context(app: Flask):
    @app.shell_context_processor
    def make_shell_context():
        from app import models

        return {"db": db, "models": models}


def _init_db(app: Flask):
    with app.app_context():
        db.create_all()
        _check_setup_redirect(app)


def _check_setup_redirect(app: Flask):
    from app.models import User

    @app.before_request
    def redirect_to_setup_if_needed():
        from flask import request

        if request.endpoint and request.endpoint in (
            "setup.wizard",
            "setup.wizard_step",
            "setup.complete",
            "setup.download_fernet_key",
            "setup.fernet_key_file",
            "static",
            "health",
        ):
            return None
        if not User.query.first():
            return redirect(url_for("setup.wizard"))
