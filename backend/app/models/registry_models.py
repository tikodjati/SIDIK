from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Klasifikasi = Literal["BIASA", "TERBATAS", "KONFIDENSIAL", "RAHASIA", "SANGAT RAHASIA"]


class RecipientIn(BaseModel):
    nrp: str = Field(min_length=3, max_length=32)
    nama: str = Field(min_length=1, max_length=128)
    pangkat: str = Field(min_length=1, max_length=64)
    jabatan: str = Field(min_length=1, max_length=128)
    satuan: str = Field(min_length=1, max_length=128)


class RecipientOut(RecipientIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DocumentIn(BaseModel):
    nomor: str = Field(min_length=1, max_length=64)
    judul: str = Field(min_length=1, max_length=256)
    klasifikasi: Klasifikasi = "RAHASIA"


class DocumentOut(DocumentIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    template: str
    created_at: datetime


class CopyRequest(BaseModel):
    recipient_id: int


class CopyIssued(BaseModel):
    copy_id: int
    document_id: int
    recipient_id: int
    issued_at: datetime
    text: str = Field(description="Naskah dengan penanda Lapis 2 untuk salinan ini")
    ledger_seq: int


class CopyOut(BaseModel):
    copy_id: int
    document_id: int
    document_nomor: str
    recipient_id: int
    recipient_nama: str
    recipient_nrp: str
    issued_at: datetime


class CopyText(BaseModel):
    copy_id: int
    text: str


class IntakeTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000, description="Teks bukti kebocoran")
    case_ref: str | None = Field(default=None, max_length=64, description="Nomor perkara/kasus")


class Attribution(BaseModel):
    copy_id: int
    recipient: RecipientOut
    document_nomor: str
    document_judul: str
    klasifikasi: str
    issued_at: datetime


class LedgerRef(BaseModel):
    seq: int
    entry_hash: str


class IntakeResult(BaseModel):
    status: Literal["IDENTIFIED", "UNREGISTERED", "INSUFFICIENT_FORENSIC_ARTIFACTS"]
    observed_bits: int
    total_bits: int
    attribution: Attribution | None = None
    ledger: LedgerRef
    note: str
    aligned_preview: str | None = Field(
        default=None, description="Foto setelah diluruskan (JPEG base64, kecil); hanya intake foto"
    )


class LedgerEntryOut(BaseModel):
    seq: int
    prev_hash: str
    entry_hash: str
    body: str
    signature: str
    key_id: str


class VerifyOut(BaseModel):
    ok: bool
    entries: int
    head_seq: int | None
    head_hash: str | None
    bad_seq: int | None = None
    reason: str | None = None
