from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Recipient(Base):
    """Penerima naskah (personel/satuan). NRP unik."""

    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(primary_key=True)
    nrp: Mapped[str] = mapped_column(String(32), unique=True)
    nama: Mapped[str] = mapped_column(String(128))
    pangkat: Mapped[str] = mapped_column(String(64))
    jabatan: Mapped[str] = mapped_column(String(128))
    satuan: Mapped[str] = mapped_column(String(128))


class Document(Base):
    """Naskah dinas master yang didistribusikan dalam beberapa salinan."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    nomor: Mapped[str] = mapped_column(String(64), unique=True)
    judul: Mapped[str] = mapped_column(String(256))
    klasifikasi: Mapped[str] = mapped_column(String(32))
    template: Mapped[str] = mapped_column(String(64), default="naskah_demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Copy(Base):
    """Satu salinan bertanda untuk satu penerima; `copy_id` acak 32 bit ditanam di payload."""

    __tablename__ = "copies"
    __table_args__ = (UniqueConstraint("document_id", "recipient_id"),)

    copy_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("recipients.id"))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    document: Mapped[Document] = relationship()
    recipient: Mapped[Recipient] = relationship()


class LedgerEntry(Base):
    """Buku besar append-only: tiap entri terikat ke entri sebelumnya lewat hash, ditandatangani."""

    __tablename__ = "ledger_entries"

    seq: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)  # diisi aplikasi
    prev_hash: Mapped[str] = mapped_column(String(64), unique=True)
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True)
    body: Mapped[str] = mapped_column(Text)  # JSON kanonik yang di-hash persis seperti tersimpan
    signature: Mapped[str] = mapped_column(String(128))
    key_id: Mapped[str] = mapped_column(String(16))


class User(Base):
    """Akun petugas. `role`: admin, distributor, atau investigator."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    full_name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(16))
    password_hash: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class UserSession(Base):
    """Sesi login; hanya hash token yang disimpan. Menghapus baris berarti mencabut sesi."""

    __tablename__ = "user_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()
