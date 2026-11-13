from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BeaconHitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    copy_id: int
    ip_address: str
    user_agent: str | None = None
    referer: str | None = None
    detected_at: datetime

    # Informasi pelengkap salinan & penerima untuk dashboard investigasi
    document_nomor: str | None = None
    recipient_nama: str | None = None
    recipient_nrp: str | None = None
    klasifikasi: str | None = None


class BeaconSimulateIn(BaseModel):
    ip_address: str = Field(default="185.220.101.5", description="IP Address penyerang/pembaca yang disimulasikan")
    user_agent: str = Field(
        default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        description="User-Agent aplikasi pembaca dokumen",
    )
    referer: str | None = Field(default=None, description="HTTP Referer (opsional)")
