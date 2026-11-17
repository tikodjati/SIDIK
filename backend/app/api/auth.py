from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE, get_current_user
from app.config import settings
from app.core.audit_ledger import Signer, append_event, get_signer
from app.core.auth import (
    burn_verification_time,
    hash_password,
    hash_token,
    new_session_token,
    utc,
    verify_password,
)
from app.db import get_session
from app.db.models import User, UserSession
from app.models.auth_models import ChangePasswordRequest, LoginRequest, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15
_BAD_LOGIN = "Nama pengguna atau kata sandi salah, atau akun sedang terkunci."


@router.post("/login", response_model=UserOut)
def login(
    body: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
) -> User:
    """Pesan gagal dan waktu responsnya sama untuk semua sebab, supaya akun tak bisa ditebak.

    Saat akun terkunci tak ada entri ledger baru, sehingga serangan menebak sandi tidak bisa
    membanjiri ledger: paling banyak MAX_FAILED_LOGINS entri per LOCK_MINUTES per akun."""
    now = datetime.now(UTC)
    user = session.scalars(select(User).where(User.username == body.username)).first()
    locked = user is not None and user.locked_until and utc(user.locked_until) > now
    if user is None or locked or not user.is_active:
        burn_verification_time(body.password)
        raise HTTPException(401, _BAD_LOGIN)

    if not verify_password(body.password, user.password_hash):
        user.failed_logins += 1
        now_locked = user.failed_logins >= MAX_FAILED_LOGINS
        if now_locked:
            user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
            user.failed_logins = 0
        data = {"username": user.username, "locked": now_locked}
        append_event(session, signer, "LOGIN_FAILED", data, user.username)
        session.commit()
        raise HTTPException(401, _BAD_LOGIN)

    user.failed_logins = 0
    user.locked_until = None
    session.execute(
        delete(UserSession).where(UserSession.user_id == user.id, UserSession.expires_at <= now)
    )
    token = new_session_token()
    expires = now + timedelta(hours=settings.session_hours)
    session.add(UserSession(token_hash=hash_token(token), user_id=user.id, expires_at=expires))
    append_event(session, signer, "LOGIN_SUCCESS", {"username": user.username}, user.username)
    session.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return user


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(get_current_user),
) -> None:
    session.execute(delete(UserSession).where(UserSession.token_hash == hash_token(token or "")))
    append_event(session, signer, "LOGOUT", {"username": user.username}, user.username)
    session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/change-password", status_code=204)
def change_password(
    body: ChangePasswordRequest,
    response: Response,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(get_current_user),
) -> None:
    """Ganti sandi sendiri dan cabut semua sesi: setelah ini admin tak lagi tahu sandinya,
    jadi nama pelaku di ledger benar-benar mewakili pemilik akun."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Kata sandi saat ini salah.")
    user.password_hash = hash_password(body.new_password)
    session.execute(delete(UserSession).where(UserSession.user_id == user.id))
    append_event(session, signer, "PASSWORD_CHANGED", {"username": user.username}, user.username)
    session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
