from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import settings


class Base(DeclarativeBase):
    pass


def _serialize_sqlite_transactions(engine: Engine) -> None:
    """SQLite (pemakaian lokal tanpa PostgreSQL): mulai tiap transaksi dengan BEGIN IMMEDIATE
    agar penulis antre. Tanpa ini dua permintaan bersamaan membaca ujung ledger yang sama dan
    bentrok di nomor urut; PostgreSQL memakai advisory lock untuk hal yang sama."""

    @event.listens_for(engine, "connect")
    def _manual_transactions(dbapi_connection, _record) -> None:
        dbapi_connection.isolation_level = None  # biarkan SQLAlchemy yang memulai transaksi

    @event.listens_for(engine, "begin")
    def _begin_immediate(connection) -> None:
        connection.exec_driver_sql("BEGIN IMMEDIATE")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(settings.database_url, connect_args={"timeout": 30})
        _serialize_sqlite_transactions(engine)
        return engine
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """Dependensi FastAPI: satu sesi per request; commit dilakukan oleh pemanggil."""
    with Session(get_engine()) as session:
        yield session
