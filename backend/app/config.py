from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIDIK_", extra="ignore")

    database_url: str = "postgresql+psycopg://sidik:sidik@localhost:5432/sidik"
    # Kunci penandatangan ledger/payload (Ed25519, PEM). Wajib diisi di luar mode dev.
    signing_key_path: str = "data/keys/ledger_ed25519.pem"
    data_dir: str = str(Path(__file__).resolve().parents[2] / "data")
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
