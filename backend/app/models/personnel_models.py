from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.registry_models import LedgerRef


class SatuanCount(BaseModel):
    satuan: str
    count: int


class PersonnelSummary(BaseModel):
    total: int
    by_satuan: list[SatuanCount]


class SeedResult(BaseModel):
    rows: int
    honey_records: int = Field(description="Honey-record tertanam di antara baris personel")


class ExportRequest(BaseModel):
    satuan: str | None = Field(default=None, max_length=128, description="Kosong = semua satuan")
    purpose: str = Field(min_length=3, max_length=256, description="Keperluan ekspor (dicatat)")


class ExportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    satuan: str | None
    purpose: str
    row_count: int
    created_at: datetime


class CorpusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    label: str
    note: str
    entries: int
    created_at: datetime


class IdentifierCounts(BaseModel):
    nik: int
    no_hp: int
    nrp: int


class DumpSource(BaseModel):
    export: ExportOut | None = Field(
        description="Ekspor asal honey-record; null = honey-record tertanam di basis data"
    )
    matched_rows: int
    proven: bool = Field(description="Bukti cukup (>= 2 baris, atau 1 baris cocok di >= 2 kolom)")


class DumpResult(BaseModel):
    status: Literal[
        "AUTHENTIC_LEAK",
        "UNTRACED_MATCH",
        "RECYCLED_PUBLIC",
        "FABRICATED",
        "NOT_FROM_OUR_DB",
        "INSUFFICIENT_DATA",
    ]
    identifiers: IdentifierCounts
    personnel_ratio: float = Field(description="Porsi identitas dump yang ada di data personel")
    corpus_ratio: float = Field(description="Porsi identitas yang ada di korpus data publik")
    corpus_label: str | None = None
    invalid_ratio: float = Field(description="Porsi NIK berformat tidak valid")
    sources: list[DumpSource] = Field(default_factory=list)
    ledger: LedgerRef
    note: str
