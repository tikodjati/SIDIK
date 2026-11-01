import pytest

pytest.importorskip("pymupdf")
pytest.importorskip("cv2")

from app.core import layer1_visual as l1  # noqa: E402
from app.core.payload import decode_scores, encode_payload  # noqa: E402
from app.core.vision_extractor import measure_slot_scores  # noqa: E402

DPI = 300
DELTA = 0.5


def test_template_lines_fit_on_page():
    for li in range(l1.LINES):
        spans = l1.word_spans(li)
        assert len(spans) == l1.WORDS_PER_LINE
        assert spans[-1][1] <= l1.PAGE_W - l1.MARGIN_L


def test_embed_then_decode_roundtrip_on_clean_render():
    frame = encode_payload(0xCAFEBABE, flags=2)
    page = l1.rasterize_gray(l1.render_pdf(frame, DELTA), DPI)
    scores = measure_slot_scores(page, DELTA, DPI)
    assert len(scores) == l1.LINES * l1.PAIRS_PER_LINE
    assert decode_scores(scores) == (0xCAFEBABE, 2)


def test_unmodulated_page_scores_near_zero():
    page = l1.rasterize_gray(l1.render_pdf(None, 0), DPI)
    scores = measure_slot_scores(page, DELTA, DPI)
    assert max(abs(s) for s in scores.values()) < 0.2
