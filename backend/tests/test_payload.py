import pytest

from app.core.payload import (
    DATA_BYTES,
    DEFAULT_NSYM,
    PayloadDecodeError,
    decode_payload,
    decode_scores,
    encode_payload,
)


def test_roundtrip():
    frame = encode_payload(0xDEADBEEF, flags=3)
    assert len(frame) == DATA_BYTES + DEFAULT_NSYM
    assert decode_payload(frame) == (0xDEADBEEF, 3)


def test_corrects_errors_up_to_half_parity():
    frame = bytearray(encode_payload(123456))
    for i in (0, 4, 7, 11):  # 4 byte rusak = batas koreksi
        frame[i] ^= 0xFF
    assert decode_payload(bytes(frame))[0] == 123456


def test_recovers_erasures_up_to_parity():
    frame = bytearray(encode_payload(987654))
    erased = list(range(8))  # 8 byte hilang = batas erasure
    for i in erased:
        frame[i] = 0
    assert decode_payload(bytes(frame), erasures=erased)[0] == 987654


def test_rejects_wrong_length():
    with pytest.raises(PayloadDecodeError):
        decode_payload(b"\x00" * 3)


def test_rejects_erasures_beyond_capacity():
    frame = encode_payload(42)
    with pytest.raises(PayloadDecodeError):
        decode_payload(frame, erasures=list(range(9)))  # 9 > nsym=8


def test_validates_inputs():
    with pytest.raises(ValueError):
        encode_payload(2**32)
    with pytest.raises(ValueError):
        encode_payload(1, flags=16)


def _scores_for(frame: bytes) -> dict[int, float]:
    bits = [(frame[n // 8] >> (7 - n % 8)) & 1 for n in range(len(frame) * 8)]
    return {n: 1.0 if b else -1.0 for n, b in enumerate(bits)}


def test_decode_scores_accepts_errors_within_reserved_margin():
    frame = bytearray(encode_payload(31337))
    for i in (0, 4, 9):  # 3 byte salah: 2E = 6 <= nsym - 2
        frame[i] ^= 0xFF
    assert decode_scores(_scores_for(bytes(frame)))[0] == 31337


def test_decode_scores_rejects_corrections_that_use_the_detection_reserve():
    frame = bytearray(encode_payload(31337))
    for i in (0, 4, 9, 12):  # 4 byte salah: masih terkoreksi oleh RS, tapi tanpa margin deteksi
        frame[i] ^= 0xFF
    with pytest.raises(PayloadDecodeError):
        decode_scores(_scores_for(bytes(frame)))
