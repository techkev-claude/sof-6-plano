import pytest
from cryptography.fernet import Fernet

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models import AppConfig, User


@pytest.fixture(scope="function")
def fresh_app():
    """App with empty DB to test setup flow."""
    config = TestingConfig()
    config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    app = create_app(config)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def fresh_client(fresh_app):
    return fresh_app.test_client()


def test_setup_redirect_on_empty_db(fresh_app, fresh_client):
    with fresh_app.app_context():
        assert User.query.count() == 0
        resp = fresh_client.get("/", follow_redirects=False)
        assert resp.status_code in (302, 308)


def test_setup_wizard_step1_renders(fresh_app, fresh_client):
    with fresh_app.app_context():
        resp = fresh_client.get("/setup/")
        assert resp.status_code == 200
        assert b"Schritt" in resp.data or b"Setup" in resp.data


def test_setup_wizard_step1_creates_user(fresh_app, fresh_client):
    with fresh_app.app_context():
        resp = fresh_client.post(
            "/setup/?step=1",
            data={
                "username": "setupadmin",
                "email": "setup@test.de",
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200


def test_fernet_key_generation():
    key = Fernet.generate_key()
    assert len(key) > 0
    f = Fernet(key)
    encrypted = f.encrypt(b"test data")
    assert f.decrypt(encrypted) == b"test data"


def test_setup_complete_config_exists(app, db):
    with app.app_context():
        value = AppConfig.get("setup_complete")
        assert value == "true"


def test_fernet_key_in_config(app, db):
    with app.app_context():
        key = AppConfig.get("fernet_key")
        assert key is not None
        f = Fernet(key.encode())
        assert f is not None


def test_setup_redirects_to_login_when_done(app, client):
    """When setup is done, /setup/ should redirect to login."""
    with app.app_context():
        resp = client.get("/setup/", follow_redirects=False)
        assert resp.status_code in (302, 308)
        assert "login" in resp.headers.get("Location", "")
