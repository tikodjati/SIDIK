from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BeaconHitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    copy_id: int
    ip_address: str
    user_agent: str | None = None
    referer: str | None = None
    webrtc_ip: str | None = None
    local_ip: str | None = None
    gpu_info: str | None = None
    cpu_cores: int | None = None
    system_language: str | None = None
    timezone: str | None = None
    screen_res: str | None = None
    raw_telemetry: str | None = None
    detected_at: datetime

    # Informasi pelengkap salinan & penerima untuk dashboard investigasi
    document_nomor: str | None = None
    recipient_nama: str | None = None
    recipient_nrp: str | None = None
    klasifikasi: str | None = None


class BeaconTelemetryIn(BaseModel):
    hit_id: int | None = None
    webrtc_ip: str | None = None
    local_ip: str | None = None
    gpu_info: str | None = None
    cpu_cores: int | None = None
    system_language: str | None = None
    timezone: str | None = None
    screen_res: str | None = None
    raw_telemetry: str | None = None


class BeaconSimulateIn(BaseModel):
    ip_address: str = Field(
        default="185.220.101.5",
        description="IP Address penyerang/pembaca yang disimulasikan (Tor Exit / VPN)",
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        description="User-Agent aplikasi pembaca dokumen",
    )
    referer: str | None = Field(default=None, description="HTTP Referer (opsional)")
    webrtc_ip: str | None = Field(
        default="114.124.210.88",
        description="IP Publik Asli (Bypass VPN via WebRTC STUN)",
    )
    local_ip: str | None = Field(
        default="192.168.1.15",
        description="IP LAN Jaringan Lokal",
    )
    gpu_info: str | None = Field(
        default="NVIDIA GeForce RTX 4070 Laptop GPU",
        description="Model Kartu Grafis / GPU",
    )
    cpu_cores: int | None = Field(default=16, description="Jumlah Core CPU")
    system_language: str | None = Field(default="id-ID", description="Bahasa Sistem")
    timezone: str | None = Field(default="Asia/Jakarta", description="Zona Waktu Perangkat")
    screen_res: str | None = Field(default="1920x1080", description="Resolusi Layar Monitor")
