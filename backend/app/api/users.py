from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, require_roles
from app.core.audit_ledger import Signer, append_event, get_signer
from app.core.auth import hash_password
from app.db import get_session
from app.db.models import User, UserSession
from app.models.auth_models import UserActiveUpdate, UserCreate, UserOut

router = APIRouter(prefix="/api/v1/users", tags=["users"])
_admin = require_roles(ADMIN)


@router.get("", response_model=list[UserOut], dependencies=[Depends(_admin)])
def list_users(session: Session = Depends(get_session)) -> list[User]:
    return list(session.scalars(select(User).order_by(User.username)))


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    admin: User = Depends(_admin),
) -> User:
    user = User(
        username=body.username,
        full_name=body.full_name,
        role=body.role,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, f"Nama pengguna {body.username} sudah dipakai") from exc
    data = {"username": user.username, "role": user.role}
    append_event(session, signer, "USER_CREATED", data, admin.username)
    session.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
def set_active(
    user_id: int,
    body: UserActiveUpdate,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    admin: User = Depends(_admin),
) -> User:
    """Aktifkan/nonaktifkan akun. Menonaktifkan langsung mencabut semua sesinya. Admin tak bisa
    menonaktifkan dirinya sendiri, jadi selalu tersisa minimal satu admin aktif."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "pengguna tidak ditemukan")
    if user.id == admin.id and not body.is_active:
        raise HTTPException(400, "Tidak bisa menonaktifkan akun sendiri.")
    user.is_active = body.is_active
    if not body.is_active:
        session.execute(delete(UserSession).where(UserSession.user_id == user.id))
    event = "USER_ACTIVATED" if body.is_active else "USER_DEACTIVATED"
    append_event(session, signer, event, {"username": user.username}, admin.username)
    session.commit()
    return user
