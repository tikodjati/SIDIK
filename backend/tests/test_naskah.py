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
        right = l1.PAGE_W - l1.MARGIN_L + 1e-6  # baris rata kanan-kiri tepat di margin
        assert all(spans[-1][1] <= right for spans in layout.spans if spans)
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


@pytest.mark.parametrize("band", [(0.5, 1.0), (0.15, 0.85)])
def test_photo_of_part_of_the_page_is_still_attributed(band):
    """Foto potongan (separuh bawah / 70% tengah, tanpa tepi kertas) tetap terbaca."""
    page = l1.rasterize_gray(naskah.copy_pdf(IDS[0], DELTA), DPI)
    h = page.shape[0]
    crop = page[int(band[0] * h) : int(band[1] * h)]
    result = naskah.decode_naskah_photo(crop, DELTA, DPI)
    assert result is not None and result.decoded[0] == IDS[0] and not result.conflict


def test_photo_of_a_few_lines_is_not_attributed_and_does_not_crash():
    """Beberapa baris saja tak cukup bit: hasilnya tak teratribusi, bukan error."""
    page = l1.rasterize_gray(naskah.copy_pdf(IDS[0], DELTA), DPI)
    h = page.shape[0]
    result = naskah.decode_naskah_photo(page[int(0.45 * h) : int(0.5 * h)], DELTA, DPI, max_tries=1)
    assert result is None or result.decoded is None


def test_clean_render_of_control_page_is_not_attributed():
    page = l1.rasterize_gray(l1.render_pdf(naskah.generic_layout(), None, 0), DPI)
    result = naskah.analyse_aligned(page, DELTA, DPI)
    assert result.decoded is None


def test_paragraph_lines_are_justified_and_last_lines_are_not():
    """Format naskah dinas: baris yang dipatahkan rata kanan-kiri, baris akhir paragraf kiri."""
    layout = naskah.layout_for(naskah.copy_choice(IDS[0]))
    right = l1.PAGE_W - l1.MARGIN_L
    assert any(layout.justified)
    for spans, justified in zip(layout.spans, layout.justified, strict=True):
        if justified:
            assert abs(spans[-1][1] - right) < 1e-6
        else:
            assert spans[-1][1] < right
