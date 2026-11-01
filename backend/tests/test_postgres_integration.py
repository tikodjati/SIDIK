"""Uji integrasi pada PostgreSQL asli (trigger append-only, penulisan paralel ledger).

Dilewati kecuali SIDIK_TEST_POSTGRES_URL diisi, mis.:
  docker run -d --rm -p 55432:5432 -e POSTGRES_USER=sidik -e POSTGRES_PASSWORD=sidik \
      -e POSTGRES_DB=sidik postgres:16-alpine
  SIDIK_TEST_POSTGRES_URL=postgresql+psycopg://sidik:sidik@localhost:55432/sidik pytest
"""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.audit_ledger import Signer, append_event, verify_chain

URL = os.environ.get("SIDIK_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="SIDIK_TEST_POSTGRES_URL tidak diisi")
BACKEND = Path(__file__).resolve().parents[1]


def _alembic(*args: str) -> None:
    env = {**os.environ, "SIDIK_DATABASE_URL": URL}
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env, check=True)


@pytest.fixture
def engine():
    _alembic("downgrade", "base")
    _alembic("upgrade", "head")  # sekaligus menguji migrasi naik-turun
    eng = create_engine(URL)
    yield eng
    eng.dispose()


def test_ledger_rejects_update_delete_and_truncate(engine):
    signer = Signer(Ed25519PrivateKey.generate())
    with Session(engine) as s:
        append_event(s, signer, "TEST", {}, "uji")
        s.commit()
    for sql in (
        "UPDATE ledger_entries SET body = 'x'",
        "DELETE FROM ledger_entries",
        "TRUNCATE ledger_entries",
    ):
        with pytest.raises(DBAPIError, match="append-only"), engine.begin() as conn:
            conn.execute(text(sql))


def test_parallel_writers_keep_a_valid_gapless_chain(engine):
    signer = Signer(Ed25519PrivateKey.generate())

    def write(i: int) -> None:
        with Session(engine) as s:
            append_event(s, signer, "KONKUREN", {"i": i}, "uji")
            s.commit()

    with ThreadPoolExecutor(30) as pool:
        list(pool.map(write, range(30)))  # satu kegagalan di sini membuat test gagal

    with Session(engine) as s:
        result = verify_chain(s, {signer.key_id: signer.public_key})
    assert result.ok and result.entries == 30 and result.head_seq == 30
