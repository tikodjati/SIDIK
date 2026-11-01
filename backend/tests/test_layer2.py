import random
from pathlib import Path

import pytest

from app.core.layer2_semantic import (
    FRAME_BITS,
    TemplateError,
    encode_text,
    extract_scores,
    load_template,
    parse_template,
)
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload

TEMPLATE = Path(__file__).resolve().parents[2] / "data" / "master_templates" / "naskah_demo.txt"


@pytest.fixture(scope="module")
def template():
    return load_template(TEMPLATE)


def test_demo_template_has_enough_capacity_for_one_frame(template):
    assert template.capacity_bits >= FRAME_BITS


def test_roundtrip(template):
    text = encode_text(template, encode_payload(0xCAFEBABE, flags=2))
    assert decode_scores(extract_scores(template, text)) == (0xCAFEBABE, 2)


def test_different_copies_have_different_text(template):
    a = encode_text(template, encode_payload(1))
    b = encode_text(template, encode_payload(2))
    assert a != b


def test_survives_case_spacing_and_punctuation_changes(template):
    text = encode_text(template, encode_payload(777))
    mangled = " ".join(text.upper().replace(".", ",").split())
    assert decode_scores(extract_scores(template, mangled))[0] == 777


def test_survives_partial_excerpt_in_any_order(template):
    text = encode_text(template, encode_payload(424242))
    lines = [ln for ln in text.splitlines() if ln.strip()]
    kept = lines[8 : 8 + int(len(lines) * 0.8)]
    random.Random(1).shuffle(kept)  # urutan tidak penting
    assert decode_scores(extract_scores(template, "\n".join(kept)))[0] == 424242


def test_tolerates_a_typo_in_a_long_variant(template):
    text = encode_text(template, encode_payload(99)).replace("menyelaraskan", "menyelarskan")
    assert decode_scores(extract_scores(template, text))[0] == 99


def test_rejects_text_without_variants(template):
    with pytest.raises(PayloadDecodeError):
        decode_scores(extract_scores(template, "Rapat hari ini membahas anggaran kantin."))


def test_rejects_too_short_excerpt(template):
    text = encode_text(template, encode_payload(5))
    with pytest.raises(PayloadDecodeError):
        decode_scores(extract_scores(template, " ".join(text.split()[:25])))


@pytest.mark.parametrize(
    "source, message",
    [
        ("{a|b|c}", "2 atau 4"),
        ("{agar|supaya} dan {agar|segera}", "ganda"),
        ("agar {agar|supaya}", "teks tetap"),
        ("{laporan|memerintahkan} {pelaporan|menugaskan}", "mirip"),
        ("{dua kata|lain}", "satu kata"),
    ],
)
def test_template_validation_rejects_bad_groups(source, message):
    with pytest.raises(TemplateError, match=message):
        parse_template(source)
