from fastapi import APIRouter

from app.core.layer2_semantic import demo_template, encode_text, extract_scores
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload
from app.models.layer2_models import (
    ExtractRequest,
    ExtractResponse,
    WatermarkRequest,
    WatermarkResponse,
)

router = APIRouter(prefix="/api/v1/layer2", tags=["layer2-semantic"])


@router.post("/watermark", response_model=WatermarkResponse)
def watermark(req: WatermarkRequest) -> WatermarkResponse:
    """Render naskah demo dengan varian frasa untuk satu salinan (tanpa DB; registri menyusul)."""
    template = demo_template()
    text = encode_text(template, encode_payload(req.copy_id, req.flags))
    return WatermarkResponse(
        text=text, slots=len(template.slots), capacity_bits=template.capacity_bits
    )


@router.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    """Baca identitas salinan dari teks bukti; menolak (tidak menebak) bila bukti tak cukup."""
    template = demo_template()
    scores = extract_scores(template, req.text)
    try:
        copy_id, flags = decode_scores(scores)
    except PayloadDecodeError:
        return ExtractResponse(
            status="INSUFFICIENT_FORENSIC_ARTIFACTS",
            observed_bits=len(scores),
            total_bits=template.capacity_bits,
        )
    return ExtractResponse(
        status="IDENTIFIED",
        copy_id=copy_id,
        flags=flags,
        observed_bits=len(scores),
        total_bits=template.capacity_bits,
    )
