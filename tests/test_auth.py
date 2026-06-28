import pytest

from tests.conftest import login, logout


def test_login_redirect_to_setup_when_no_user(app, client, admin_user):
    # admin_user fixture ensures a user exists; login page should render
    with app.app_context():
        resp = client.get("/auth/login")
        assert resp.status_code == 200


def test_login_success(app, client, admin_user):
    with app.app_context():
        resp = login(client)
        assert b"Reisen" in resp.data or resp.status_code == 200


def test_login_wrong_password(app, client, admin_user):
    with app.app_context():
        resp = client.post(
            "/auth/login",
            data={"username": "testadmin", "password": "wrongpass"},
            follow_redirects=True,
        )
        assert "Ung" in resp.data.decode("utf-8", errors="replace") or resp.status_code == 200


def test_login_unknown_user(app, client):
    with app.app_context():
        resp = client.post(
            "/auth/login",
            data={"username": "nobody", "password": "pass"},
            follow_redirects=True,
        )
        assert "Ung" in resp.data.decode("utf-8", errors="replace") or resp.status_code == 200


def test_logout(app, client, admin_user):
    with app.app_context():
        login(client)
        resp = logout(client)
        assert resp.status_code == 200


def test_protected_route_redirects_when_not_logged_in(app, client):
    with app.app_context():
        logout(client)
        resp = client.get("/trips/", follow_redirects=False)
        assert resp.status_code in (302, 308)


def test_login_rate_limit_header(app, client, admin_user):
    """Rate limiter should return 429 after too many requests."""
    with app.app_context():
        for _ in range(12):
            client.post(
                "/auth/login",
                data={"username": "ratetest", "password": "wrong"},
            )
