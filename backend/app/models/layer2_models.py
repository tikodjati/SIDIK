from typing import Literal

from pydantic import BaseModel, Field


class WatermarkRequest(BaseModel):
    copy_id: int = Field(ge=0, lt=2**32, description="ID salinan (NRP/penerima dicari lewat DB)")
    flags: int = Field(default=0, ge=0, lt=16)


class WatermarkResponse(BaseModel):
    text: str
    slots: int
    capacity_bits: int


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000, description="Teks bukti (ketikan ulang)")


class ExtractResponse(BaseModel):
    status: Literal["IDENTIFIED", "INSUFFICIENT_FORENSIC_ARTIFACTS"]
    copy_id: int | None = None
    flags: int | None = None
    observed_bits: int
    total_bits: int
