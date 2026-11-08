import pytest

pytest.importorskip("pymupdf")
pytest.importorskip("cv2")

from app.core import layer1_visual as l1  # noqa: E402
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload  # noqa: E402
from app.core.vision_extractor import measure_slot_scores  # noqa: E402

DPI = 300
DELTA = 0.5
LAYOUTS = [l1.spike_layout, l1.naskah_layout]


@pytest.mark.parametrize("make_layout", LAYOUTS)
def test_layout_fits_on_page_and_carries_at_least_one_frame(make_layout):
    layout = make_layout()
    assert all(spans[-1][1] <= l1.PAGE_W - l1.MARGIN_L for spans in layout.spans)
    assert layout.baselines[-1] <= l1.PAGE_H - l1.MARGIN_T
    assert layout.total_slots >= 104  # satu frame payload penuh


@pytest.mark.parametrize("make_layout", LAYOUTS)
def test_embed_then_decode_roundtrip_on_clean_render(make_layout):
    layout = make_layout()
    frame = encode_payload(0xCAFEBABE, flags=2)
    page = l1.rasterize_gray(l1.render_pdf(layout, frame, DELTA), DPI)
    scores = measure_slot_scores(page, layout, DELTA, DPI)
    assert len(scores) == layout.total_slots
    assert decode_scores(scores) == (0xCAFEBABE, 2)


@pytest.mark.parametrize("make_layout", LAYOUTS)
def test_unmodulated_page_scores_near_zero(make_layout):
    layout = make_layout()
    page = l1.rasterize_gray(l1.render_pdf(layout, None, 0), DPI)
    scores = measure_slot_scores(page, layout, DELTA, DPI)
    assert max(abs(s) for s in scores.values()) < 0.2


def test_naskah_pdf_text_does_not_decode_as_a_layer2_identity():
    """Teks PDF (varian pertama di semua slot) bila diketik ulang tak boleh menuduh siapa pun."""
    from app.core.layer2_semantic import demo_template, extract_scores

    text = " ".join(" ".join(words) for words in l1.naskah_layout().lines)
    with pytest.raises(PayloadDecodeError):
        decode_scores(extract_scores(demo_template(), text))
