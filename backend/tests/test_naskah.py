"""Naskah terpadu: PDF salinan membawa Lapis 1 (spasi) dan Lapis 2 (pilihan kata)."""

import pytest

pymupdf = pytest.importorskip("pymupdf")
pytest.importorskip("cv2")

from app.core import layer1_visual as l1  # noqa: E402
from app.core import naskah  # noqa: E402
from app.core.layer2_semantic import demo_template, extract_scores  # noqa: E402
from app.core.payload import PayloadDecodeError, decode_scores  # noqa: E402

DPI = 300
DELTA = 0.5
IDS = (0x1A2B3C4D, 0xDEADBEEF)


def _pdf_text(pdf: bytes) -> str:
    return pymupdf.open(stream=pdf, filetype="pdf")[0].get_text()


def test_line_breaks_are_identical_for_every_copy_and_fit_the_page():
    layouts = [naskah.generic_layout()] + [naskah.layout_for(naskah.copy_choice(i)) for i in IDS]
    shape = [len(words) for words in layouts[0].lines]
    for layout in layouts:
        assert [len(words) for words in layout.lines] == shape
        assert layout.baselines == layouts[0].baselines
        assert all(spans[-1][1] <= l1.PAGE_W - l1.MARGIN_L for spans in layout.spans if spans)
        assert layout.baselines[-1] <= l1.PAGE_H - l1.MARGIN_T
    assert layouts[1].lines != layouts[2].lines  # kata varian memang berbeda per salinan


@pytest.mark.parametrize("copy_id", IDS)
def test_text_copied_from_copy_pdf_decodes_to_that_copy(copy_id):
    text = _pdf_text(naskah.copy_pdf(copy_id, DELTA))
    assert decode_scores(extract_scores(demo_template(), text))[0] == copy_id


def test_generic_text_does_not_decode_as_an_identity():
    """Varian pertama di semua slot (PDF kontrol) bila diketik ulang tak boleh menuduh siapa pun."""
    text = _pdf_text(l1.render_pdf(naskah.generic_layout(), None, 0))
    with pytest.raises(PayloadDecodeError):
        decode_scores(extract_scores(demo_template(), text))


@pytest.mark.parametrize("copy_id", IDS)
def test_clean_render_reads_every_variant_and_both_layers(copy_id):
    page = l1.rasterize_gray(naskah.copy_pdf(copy_id, DELTA), DPI)
    result = naskah.analyse_aligned(page, DELTA, DPI)
    assert result.layer1_decoded[0] == copy_id
    assert result.layer2_decoded[0] == copy_id
    assert len(result.layer2_scores) == demo_template().capacity_bits  # semua varian terbaca
    assert result.decoded[0] == copy_id and not result.conflict


def test_clean_render_with_mixed_identities_is_a_conflict():
    from app.core.payload import encode_payload

    words = naskah.layout_for(naskah.copy_choice(IDS[0]))
    page = l1.rasterize_gray(l1.render_pdf(words, encode_payload(IDS[1]), DELTA), DPI)
    result = naskah.analyse_aligned(page, DELTA, DPI)
    assert result.conflict and result.decoded is None


def test_clean_render_of_control_page_is_not_attributed():
    page = l1.rasterize_gray(l1.render_pdf(naskah.generic_layout(), None, 0), DPI)
    result = naskah.analyse_aligned(page, DELTA, DPI)
    assert result.decoded is None
