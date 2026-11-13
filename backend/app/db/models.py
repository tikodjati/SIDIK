from datetime import UTC, date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
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
    # Four-eyes: salinan naskah RAHASIA/SANGAT RAHASIA mulai PENDING dan baru ISSUED setelah
    # disetujui admin lain (bukan pengaju). REJECTED = ditolak, tak pernah diedarkan.
    status: Mapped[str] = mapped_column(String(16), default="ISSUED", server_default="ISSUED")
    requested_by: Mapped[str | None] = mapped_column(String(32), default=None)
    approved_by: Mapped[str | None] = mapped_column(String(32), default=None)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    document: Mapped[Document] = relationship()
    recipient: Mapped[Recipient] = relationship()
    tokens: Mapped[list["HoneyTokenRow"]] = relationship(
        back_populates="copy", order_by="HoneyTokenRow.token_index"
    )


class HoneyTokenRow(Base):
    """Honey-token Lapis 3: angka fiktif khusus satu salinan. `digits` (angka tanpa tanda baca)
    unik global, jadi satu angka di bukti menunjuk tepat satu salinan."""

    __tablename__ = "honey_tokens"
    __table_args__ = (UniqueConstraint("copy_id", "token_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    copy_id: Mapped[int] = mapped_column(ForeignKey("copies.copy_id"), index=True)
    token_index: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(String(32))  # seperti tercetak, mis. "143.275"
    digits: Mapped[str] = mapped_column(String(32), unique=True)  # "143275"

    copy: Mapped[Copy] = relationship(back_populates="tokens")


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


class Personnel(Base):
    """Data personel (demo pengganti SISFO). Sebagian baris adalah honey-record tertanam yang
    tak bisa dibedakan dari luar; katalognya hanya ada di `honey_records`."""

    __tablename__ = "personnel"

    id: Mapped[int] = mapped_column(primary_key=True)
    nrp: Mapped[str] = mapped_column(String(32), unique=True)
    nama: Mapped[str] = mapped_column(String(128))
    pangkat: Mapped[str] = mapped_column(String(64))
    satuan: Mapped[str] = mapped_column(String(128), index=True)
    nik: Mapped[str] = mapped_column(String(16), unique=True)
    no_hp: Mapped[str] = mapped_column(String(16), unique=True)
    tanggal_lahir: Mapped[date] = mapped_column(Date)


class DataExport(Base):
    """Satu ekspor data personel oleh petugas; memuat honey-record khusus ekspor ini."""

    __tablename__ = "data_exports"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32))
    satuan: Mapped[str | None] = mapped_column(String(128), default=None)  # None = semua satuan
    purpose: Mapped[str] = mapped_column(String(256))
    row_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class HoneyRecord(Base):
    """Honey-record Lapis 4: persona rekaan. `export_id` None = tertanam di tabel personel."""

    __tablename__ = "honey_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    export_id: Mapped[int | None] = mapped_column(
        ForeignKey("data_exports.id"), default=None, index=True
    )
    nrp: Mapped[str] = mapped_column(String(32), unique=True)
    nama: Mapped[str] = mapped_column(String(128))
    pangkat: Mapped[str] = mapped_column(String(64))
    satuan: Mapped[str] = mapped_column(String(128))
    nik: Mapped[str] = mapped_column(String(16), unique=True)
    no_hp: Mapped[str] = mapped_column(String(16), unique=True)
    tanggal_lahir: Mapped[date] = mapped_column(Date)

    export: Mapped[DataExport | None] = relationship()


class PublicCorpus(Base):
    """Kumpulan data publik/bocoran lama yang sudah dikenal (untuk deteksi daur ulang)."""

    __tablename__ = "public_corpora"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(128), unique=True)
    note: Mapped[str] = mapped_column(String(256), default="")
    entries: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CorpusFingerprint(Base):
    """Hash SHA-256 satu identitas (NIK/HP) dari korpus publik; data aslinya tidak disimpan."""

    __tablename__ = "corpus_fingerprints"
    __table_args__ = (UniqueConstraint("corpus_id", "fp"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    corpus_id: Mapped[int] = mapped_column(ForeignKey("public_corpora.id"))
    fp: Mapped[str] = mapped_column(String(64), index=True)


class BeaconHit(Base):
    """Mencatat suar pelacak (Canary Token) yang terpicu saat salinan naskah dibuka."""

    __tablename__ = "beacon_hits"

    id: Mapped[int] = mapped_column(primary_key=True)
    copy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("copies.copy_id"), index=True)
    ip_address: Mapped[str] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512), default=None)
    referer: Mapped[str | None] = mapped_column(String(256), default=None)
    webrtc_ip: Mapped[str | None] = mapped_column(String(128), default=None)
    local_ip: Mapped[str | None] = mapped_column(String(128), default=None)
    gpu_info: Mapped[str | None] = mapped_column(String(256), default=None)
    cpu_cores: Mapped[int | None] = mapped_column(Integer, default=None)
    system_language: Mapped[str | None] = mapped_column(String(64), default=None)
    timezone: Mapped[str | None] = mapped_column(String(64), default=None)
    screen_res: Mapped[str | None] = mapped_column(String(64), default=None)
    raw_telemetry: Mapped[str | None] = mapped_column(Text, default=None)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    copy: Mapped[Copy] = relationship()
