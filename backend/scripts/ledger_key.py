"""Buat kunci ledger Ed25519 baru dan cetak sebagai PEM satu baris (`\\n` literal), siap ditempel
ke variabel lingkungan SIDIK_SIGNING_KEY_PEM di dashboard hosting.

    python -m scripts.ledger_key

Simpan hasilnya di pengelola kata sandi. Kunci ini menandatangani seluruh audit trail: bila hilang
atau diganti, penulisan ke database yang sama akan ditolak. Jangan dibuat ulang untuk database
yang sudah berisi entri. Jangan dimasukkan ke git atau dibagikan di grup."""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.core.audit_ledger import Signer


def main() -> None:
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    print(f"ID kunci: {Signer(key).key_id}")
    print("Nilai SIDIK_SIGNING_KEY_PEM (satu baris):")
    print(pem.strip().replace("\n", "\\n"))


if __name__ == "__main__":
    main()
