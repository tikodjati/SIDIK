from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIDIK_", extra="ignore")

    database_url: str = "postgresql+psycopg://sidik:sidik@localhost:5432/sidik"
    # Kunci penandatangan ledger/payload (Ed25519, PEM). Wajib diisi di luar mode dev.
    signing_key_path: str = str(
        Path(__file__).resolve().parents[2] / "data" / "keys" / "ledger_ed25519.pem"
    )
    # Database bersama: false agar server tanpa berkas kunci tim gagal jelas, bukan membuat
    # kunci baru yang entrinya tak bisa diverifikasi anggota tim lain.
    signing_key_autocreate: bool = True
    data_dir: str = str(Path(__file__).resolve().parents[2] / "data")
    cors_origins: list[str] = ["http://localhost:3000"]
    session_hours: int = 8
    # Wajib true bila dilayani lewat HTTPS; false hanya untuk http://localhost saat pengembangan.
    cookie_secure: bool = False
    # Amplitudo modulasi spasi Lapis 1 pada PDF salinan (pt). Uji foto asli: 0,3 dan 0,5 terbaca.
    layer1_delta_pt: float = 0.5
    max_photo_mb: int = 15


    @field_validator("database_url")
    @classmethod
    def _psycopg_driver(cls, url: str) -> str:
        """URL dari penyedia (Neon dsb.) biasanya `postgresql://`; SQLAlchemy perlu nama driver."""
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


settings = Settings()
