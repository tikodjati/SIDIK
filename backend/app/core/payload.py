"""Payload identitas salinan dokumen: copy_id + Reed-Solomon GF(2^8).

Payload sengaja hanya memuat ID salinan; NRP, satuan, dan waktu dicari lewat DB.
Frame data (5 byte) = versi/flags (8 bit) || copy_id (32 bit), lalu ditambah paritas RS.
Dengan nsym=8: koreksi hingga 4 byte salah (error) atau 8 byte hilang (erasure),
secara umum 2E + S <= nsym.
"""

import struct

import numpy as np
from reedsolo import ReedSolomonError, RSCodec

DATA_BYTES = 5
DEFAULT_NSYM = 8
VERSION = 1


class PayloadDecodeError(Exception):
    """Payload tidak dapat dipulihkan (kerusakan melebihi kapasitas koreksi)."""


def encode_payload(copy_id: int, flags: int = 0, nsym: int = DEFAULT_NSYM) -> bytes:
    if not 0 <= copy_id < 2**32:
        raise ValueError("copy_id harus 32 bit tak bertanda")
    if not 0 <= flags < 16:
        raise ValueError("flags harus 4 bit (0-15)")
    header = (VERSION << 4) | flags
    return bytes(RSCodec(nsym).encode(struct.pack(">BI", header, copy_id)))


def decode_payload(
    frame: bytes, erasures: list[int] | None = None, nsym: int = DEFAULT_NSYM
) -> tuple[int, int]:
    """Kembalikan (copy_id, flags). `erasures` = indeks byte yang diketahui hilang."""
    if len(frame) != DATA_BYTES + nsym:
        raise PayloadDecodeError("panjang frame tidak sesuai")
    try:
        decoded = RSCodec(nsym).decode(frame, erase_pos=erasures or [])[0]
    except ReedSolomonError as exc:
        raise PayloadDecodeError(str(exc)) from exc
    header, copy_id = struct.unpack(">BI", bytes(decoded))
    if header >> 4 != VERSION:
        raise PayloadDecodeError("versi payload tidak dikenal")
    return copy_id, header & 0x0F


DETECTION_RESERVE = 2  # simbol paritas yang disisakan untuk mendeteksi salah-koreksi


def decode_scores(
    scores: dict[int, float], nbits: int = (DATA_BYTES + DEFAULT_NSYM) * 8
) -> tuple[int, int]:
    """Gabungkan skor bit dari lapis mana pun (soft vote) lalu koreksi dengan Reed-Solomon.

    `scores[n]` = bukti untuk bit ke-n pada urutan slot; bit payload = n mod `nbits`, jadi frame
    berulang bila slot lebih banyak dari `nbits`. Nilai positif = bit 1, negatif = bit 0.
    Byte yang bitnya tidak seluruhnya teramati dianggap erasure.

    Kebijakan zero false-accusation: kapasitas koreksi penuh (2E + S <= nsym) tidak dipakai.
    Hasil ditolak jika 2E + S > nsym - DETECTION_RESERVE, karena dekode yang memakai seluruh
    paritas dapat salah-koreksi ke kata sandi lain (ID salah) pada bukti yang rusak berat."""
    acc = np.zeros(nbits)
    cnt = np.zeros(nbits)
    for n, s in scores.items():
        acc[n % nbits] += np.clip(s, -1.5, 1.5)
        cnt[n % nbits] += 1
    bits = (acc > 0).astype(np.uint8)
    erasures = [i for i in range(nbits // 8) if not cnt[i * 8 : i * 8 + 8].all()]
    if len(erasures) > DEFAULT_NSYM - DETECTION_RESERVE:
        raise PayloadDecodeError("terlalu banyak byte tanpa observasi")
    received = np.packbits(bits).tobytes()
    copy_id, flags = decode_payload(received, erasures=erasures)
    corrected = encode_payload(copy_id, flags)
    errors = sum(
        1 for i in range(len(received)) if i not in erasures and received[i] != corrected[i]
    )
    if 2 * errors + len(erasures) > DEFAULT_NSYM - DETECTION_RESERVE:
        raise PayloadDecodeError("kerusakan terlalu dekat dengan batas koreksi; ditolak")
    return copy_id, flags
