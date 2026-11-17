"""Kelola akun dari baris perintah (tak ada akun bawaan; akun pertama dibuat di sini).

Jalankan dari backend/ (atau: docker compose exec api python -m scripts.users ...):
  python -m scripts.users create --username admin --full-name "Nama Admin" --role admin
  python -m scripts.users seed-demo

`create` meminta kata sandi tanpa menampilkannya (atau baca dari stdin dengan --password-stdin).
`seed-demo` membuat satu akun per peran dengan sandi acak dan menulisnya ke
<data>/keys/demo_users.txt (diabaikan git). Khusus demo; jangan dipakai di lingkungan nyata.
"""

import argparse
import getpass
import secrets
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ROLES
from app.config import settings
from app.core.audit_ledger import append_event, get_signer
from app.core.auth import hash_password
from app.db import get_engine
from app.db.models import User
from app.models.auth_models import PASSWORD_MIN, UserCreate

DEMO_USERS = {
    "admin": ("Admin Demo", "admin"),
    "distributor": ("Distributor Demo", "distributor"),
    "investigator": ("Investigator Demo", "investigator"),
}


def _create(session: Session, body: UserCreate) -> None:
    session.add(
        User(
            username=body.username,
            full_name=body.full_name,
            role=body.role,
            password_hash=hash_password(body.password),
        )
    )
    session.flush()
    data = {"username": body.username, "role": body.role}
    append_event(session, get_signer(), "USER_CREATED", data, "cli")


def _exists(session: Session, username: str) -> bool:
    return session.scalars(select(User).where(User.username == username)).first() is not None


def create(args: argparse.Namespace) -> None:
    if args.password_stdin:
        password = sys.stdin.readline().rstrip("\r\n")
    else:
        password = getpass.getpass("Kata sandi: ")
        if password != getpass.getpass("Ulangi kata sandi: "):
            sys.exit("Kata sandi tidak sama.")
    if len(password) < PASSWORD_MIN:
        sys.exit(f"Kata sandi minimal {PASSWORD_MIN} karakter.")
    body = UserCreate(
        username=args.username, full_name=args.full_name, role=args.role, password=password
    )
    with Session(get_engine()) as session:
        if _exists(session, body.username):
            sys.exit(f"Nama pengguna {body.username} sudah ada.")
        _create(session, body)
        session.commit()
    print(f"Akun {body.username} ({body.role}) dibuat.")


def seed_demo(_: argparse.Namespace) -> None:
    out = Path(settings.data_dir) / "keys" / "demo_users.txt"
    lines = []
    with Session(get_engine()) as session:
        for username, (full_name, role) in DEMO_USERS.items():
            if _exists(session, username):
                print(f"{username} sudah ada, dilewati.")
                continue
            password = secrets.token_urlsafe(12)
            _create(
                session,
                UserCreate(username=username, full_name=full_name, role=role, password=password),
            )
            lines.append(f"{username} {password}\n")
        session.commit()
    if lines:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as f:
            f.writelines(lines)
    print(f"{len(lines)} akun demo dibuat. Kredensial: {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--username", required=True)
    c.add_argument("--full-name", required=True)
    c.add_argument("--role", required=True, choices=ROLES)
    c.add_argument("--password-stdin", action="store_true")
    c.set_defaults(func=create)
    sub.add_parser("seed-demo").set_defaults(func=seed_demo)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
