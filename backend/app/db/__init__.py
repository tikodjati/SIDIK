from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """Dependensi FastAPI: satu sesi per request; commit dilakukan oleh pemanggil."""
    with Session(get_engine()) as session:
        yield session
