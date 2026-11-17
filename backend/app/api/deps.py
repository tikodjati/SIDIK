from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import hash_token, utc
from app.db import get_session
from app.db.models import User, UserSession

ADMIN = "admin"
DISTRIBUTOR = "distributor"
INVESTIGATOR = "investigator"
ROLES = (ADMIN, DISTRIBUTOR, INVESTIGATOR)

SESSION_COOKIE = "sidik_session"


def get_current_user(
    token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    session: Session = Depends(get_session),
) -> User:
    unauthorized = HTTPException(401, "Belum login atau sesi berakhir.")
    if not token:
        raise unauthorized
    row = session.get(UserSession, hash_token(token))
    if row is None or utc(row.expires_at) <= datetime.now(UTC) or not row.user.is_active:
        raise unauthorized
    return row.user


def require_roles(*roles: str) -> Callable[..., User]:
    """Dependensi yang menolak (403) pengguna di luar `roles`."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Peran Anda tidak diizinkan untuk tindakan ini.")
        return user

    return dependency
