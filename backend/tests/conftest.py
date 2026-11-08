import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import auth
from app.core.audit_ledger import Signer, get_signer
from app.db import Base, get_session, models
from app.main import app

TEST_PASSWORD = "sandi-uji-panjang"


@pytest.fixture(autouse=True)
def fast_password_hash(monkeypatch):
    """scrypt penuh sengaja lambat; test memakai biaya rendah."""
    monkeypatch.setattr(auth, "SCRYPT_N", 2**8)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def signer():
    return Signer(Ed25519PrivateKey.generate())


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def anon(engine, signer):
    """Klien tanpa login."""

    def _session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_signer] = lambda: signer
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def login_as(anon, engine):
    """Pabrik klien yang sudah login dengan peran tertentu (akun dibuat bila belum ada)."""

    def _login(role: str, username: str | None = None) -> TestClient:
        username = username or role
        with Session(engine) as s:
            s.add(
                models.User(
                    username=username,
                    full_name=f"Uji {role}",
                    role=role,
                    password_hash=auth.hash_password(TEST_PASSWORD),
                )
            )
            s.commit()
        client = TestClient(app)
        res = client.post(
            "/api/v1/auth/login", json={"username": username, "password": TEST_PASSWORD}
        )
        assert res.status_code == 200, res.text
        return client

    return _login


@pytest.fixture
def client(login_as):
    """Klien admin: boleh semua, untuk test yang tidak menguji peran."""
    return login_as("admin")
