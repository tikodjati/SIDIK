import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.auth import MAX_FAILED_LOGINS
from app.api.deps import SESSION_COOKIE
from app.core import auth
from app.db.models import LedgerEntry, User, UserSession
from app.main import app
from tests.conftest import TEST_PASSWORD

# Rute yang sengaja terbuka. Rute baru otomatis wajib login kecuali ditambahkan di sini.
PUBLIC = {("GET", "/health"), ("POST", "/api/v1/auth/login")}

# Matriks peran: (metode, path) -> peran yang boleh. Rute baru wajib dicantumkan.
A, D, INV = "admin", "distributor", "investigator"
ALLOWED = {
    ("POST", "/api/v1/auth/logout"): {A, D, INV},
    ("GET", "/api/v1/auth/me"): {A, D, INV},
    ("POST", "/api/v1/auth/change-password"): {A, D, INV},
    ("GET", "/api/v1/users"): {A},
    ("POST", "/api/v1/users"): {A},
    ("PATCH", "/api/v1/users/{user_id}"): {A},
    ("POST", "/api/v1/layer2/watermark"): {A},
    ("POST", "/api/v1/layer2/extract"): {A, INV},
    ("POST", "/api/v1/recipients"): {A, D},
    ("GET", "/api/v1/recipients"): {A, D},
    ("GET", "/api/v1/documents"): {A, D},
    ("POST", "/api/v1/documents"): {A, D},
    ("GET", "/api/v1/copies"): {A, D},
    ("GET", "/api/v1/copies/{copy_id}/text"): {A},
    ("GET", "/api/v1/copies/{copy_id}/pdf"): {A, D},
    ("POST", "/api/v1/intake/photo"): {A, INV},
    ("POST", "/api/v1/documents/{document_id}/copies"): {A, D},
    ("POST", "/api/v1/intake/text"): {A, INV},
    ("GET", "/api/v1/ledger"): {A, INV},
    ("GET", "/api/v1/ledger/verify"): {A, INV},
    ("GET", "/api/v1/personnel/summary"): {A, D},
    ("POST", "/api/v1/personnel/seed-demo"): {A},
    ("POST", "/api/v1/personnel/exports"): {A, D},
    ("GET", "/api/v1/personnel/exports"): {A, D, INV},
    ("POST", "/api/v1/corpora"): {A},
    ("GET", "/api/v1/corpora"): {A, INV},
    ("POST", "/api/v1/intake/dump"): {A, INV},
}


def _routes():
    # Dari skema OpenAPI: app.routes tidak selalu memuat rute dari include_router.
    return {
        (method.upper(), path)
        for path, item in app.openapi()["paths"].items()
        for method in item
    }


def _url(path: str) -> str:
    return path.replace("{user_id}", "1").replace("{copy_id}", "1").replace("{document_id}", "1")


def test_every_route_is_either_public_or_in_the_role_matrix():
    routes = _routes()
    assert len(routes) > 15  # pengaman: pastikan rute router benar-benar terbaca
    assert routes == PUBLIC | set(ALLOWED)


@pytest.mark.parametrize("route", sorted(ALLOWED))
def test_protected_routes_reject_anonymous(anon, route):
    method, path = route
    assert anon.request(method, _url(path), json={}).status_code == 401


@pytest.mark.parametrize("role", [A, D, INV])
@pytest.mark.parametrize("route", sorted(ALLOWED))
def test_role_matrix_is_enforced(login_as, role, route):
    method, path = route
    if path.endswith(("logout", "change-password")):
        pytest.skip("mengubah sesi; diuji terpisah")
    status = login_as(role).request(method, _url(path), json={}).status_code
    if role in ALLOWED[route]:
        assert status != 403  # boleh lewat RBAC (404/422 karena data uji kosong itu wajar)
    else:
        assert status == 403


def _login(client, username, password=TEST_PASSWORD):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def _events(session):
    entries = session.scalars(select(LedgerEntry).order_by(LedgerEntry.seq))
    return [json.loads(e.body) for e in entries]


def test_login_sets_httponly_strict_cookie_and_me_returns_user(anon, login_as):
    login_as(D, "budi")
    res = _login(anon, "budi")
    cookie = res.headers["set-cookie"].lower()
    assert SESSION_COOKIE in cookie and "httponly" in cookie and "samesite=strict" in cookie
    assert "password" not in res.text
    assert anon.get("/api/v1/auth/me").json()["username"] == "budi"


def test_failed_login_message_does_not_reveal_whether_account_exists(anon, login_as):
    login_as(D, "budi")
    wrong = _login(anon, "budi", "bukan-sandinya-x")
    missing = _login(anon, "tidak-ada", "bukan-sandinya-x")
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json() == missing.json()


def test_session_token_is_stored_only_as_hash(anon, login_as, session):
    login_as(D, "budi")
    token = _login(anon, "budi").cookies[SESSION_COOKIE]
    stored = {row.token_hash for row in session.scalars(select(UserSession))}
    assert token not in stored and auth.hash_token(token) in stored


def test_account_locks_after_repeated_failures_then_ledger_stops_growing(anon, login_as, session):
    login_as(D, "budi")
    for _ in range(MAX_FAILED_LOGINS):
        assert _login(anon, "budi", "bukan-sandinya-x").status_code == 401
    before = len(_events(session))
    assert _login(anon, "budi").status_code == 401  # sandi benar pun ditolak saat terkunci
    assert _login(anon, "budi", "bukan-sandinya-x").status_code == 401
    assert len(_events(session)) == before  # tak bisa membanjiri ledger
    assert _events(session)[-1]["data"]["locked"] is True


def test_lock_expires(anon, login_as, engine):
    login_as(D, "budi")
    for _ in range(MAX_FAILED_LOGINS):
        _login(anon, "budi", "bukan-sandinya-x")
    with Session(engine) as s:
        past = datetime.now(UTC) - timedelta(minutes=1)
        s.execute(update(User).where(User.username == "budi").values(locked_until=past))
        s.commit()
    assert _login(anon, "budi").status_code == 200


def test_expired_session_is_rejected(login_as, engine):
    client = login_as(D, "budi")
    with Session(engine) as s:
        s.execute(update(UserSession).values(expires_at=datetime.now(UTC) - timedelta(seconds=1)))
        s.commit()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_revokes_the_session_on_the_server(login_as):
    client = login_as(D, "budi")
    cookie = client.cookies[SESSION_COOKIE]
    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.set(SESSION_COOKIE, cookie)  # cookie curian tak berlaku lagi
    assert client.get("/api/v1/auth/me").status_code == 401


def test_change_password_requires_current_and_revokes_sessions(anon, login_as):
    client = login_as(D, "budi")
    body = {"current_password": "salah-sekali-x", "new_password": "sandi-baru-panjang"}
    assert client.post("/api/v1/auth/change-password", json=body).status_code == 400
    body["current_password"] = TEST_PASSWORD
    assert client.post("/api/v1/auth/change-password", json=body).status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    assert _login(anon, "budi").status_code == 401
    assert _login(anon, "budi", "sandi-baru-panjang").status_code == 200


def test_admin_creates_user_and_weak_or_bad_input_is_rejected(client, anon):
    body = {"username": "sari", "full_name": "Sari", "role": INV, "password": "sandi-sari-panjang"}
    res = client.post("/api/v1/users", json=body)
    assert res.status_code == 201 and "password" not in res.text
    assert client.post("/api/v1/users", json=body).status_code == 409
    for bad in (
        {"username": "x2", "password": "pendek"},
        {"username": "SARI BESAR"},
        {"username": "x3", "role": "root"},
    ):
        assert client.post("/api/v1/users", json={**body, **bad}).status_code == 422
    assert _login(anon, "sari", "sandi-sari-panjang").json()["role"] == INV


def test_deactivating_a_user_kills_sessions_and_blocks_login(client, login_as, anon, session):
    target = login_as(D, "budi")
    uid = target.get("/api/v1/auth/me").json()["id"]
    assert client.patch(f"/api/v1/users/{uid}", json={"is_active": False}).status_code == 200
    assert target.get("/api/v1/auth/me").status_code == 401
    assert _login(anon, "budi").status_code == 401
    assert _events(session)[-1]["event"] == "USER_DEACTIVATED"
    assert client.patch(f"/api/v1/users/{uid}", json={"is_active": True}).status_code == 200
    assert _login(anon, "budi").status_code == 200


def test_admin_cannot_deactivate_self(client):
    me = client.get("/api/v1/auth/me").json()["id"]
    assert client.patch(f"/api/v1/users/{me}", json={"is_active": False}).status_code == 400


def test_ledger_actor_comes_from_login_and_x_actor_header_is_ignored(login_as, session):
    client = login_as(INV, "sari")
    res = client.post(
        "/api/v1/intake/text", json={"text": "teks bebas"}, headers={"X-Actor": "Kolonel Palsu"}
    )
    assert res.status_code == 200
    last = _events(session)[-1]
    assert last["event"] == "LEAK_INTAKE_TEXT" and last["actor"] == "sari"


def test_password_hash_roundtrip_and_stored_parameters_survive_cost_change(monkeypatch):
    stored = auth.hash_password("rahasia-panjang-1")
    monkeypatch.setattr(auth, "SCRYPT_N", 2**9)
    assert auth.verify_password("rahasia-panjang-1", stored)
    assert not auth.verify_password("rahasia-panjang-2", stored)
    assert not auth.verify_password("x", "bukan-hash")
