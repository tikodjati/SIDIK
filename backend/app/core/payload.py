"""Payload identitas salinan dokumen: copy_id + Reed-Solomon GF(2^8).

Payload sengaja hanya memuat ID salinan; NRP, satuan, dan waktu dicari lewat DB.
Frame data (5 byte) = versi/flags (8 bit) || copy_id (32 bit), lalu ditambah paritas RS.
Dengan nsym=8: koreksi hingga 4 byte salah (error) atau 8 byte hilang (erasure),
secara umum 2E + S <= nsym.
"""

import struct

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
