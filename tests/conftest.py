import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models import AppConfig, User


@pytest.fixture(scope="session")
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        _seed_config()
        yield app
        _db.drop_all()


@pytest.fixture(scope="session")
def db(app):
    return _db


@pytest.fixture(scope="function")
def session(db):
    connection = db.engine.connect()
    transaction = connection.begin()
    db.session.bind = connection
    yield db.session
    db.session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def admin_user(app, db):
    with app.app_context():
        user = User.query.filter_by(username="testadmin").first()
        if not user:
            user = User(username="testadmin", email="admin@test.de", is_admin=True)
            user.set_password("testpass123")
            db.session.add(user)
            db.session.commit()
        return user


def _seed_config():
    from cryptography.fernet import Fernet
    configs = {
        "fernet_key": Fernet.generate_key().decode(),
        "setup_complete": "true",
        "ai_provider": "anthropic",
    }
    for k, v in configs.items():
        if not AppConfig.query.filter_by(key=k).first():
            _db.session.add(AppConfig(key=k, value=v))
    _db.session.commit()


def login(client, username="testadmin", password="testpass123"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    return client.get("/auth/logout", follow_redirects=True)
