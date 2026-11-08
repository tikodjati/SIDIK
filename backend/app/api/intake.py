import base64
import hashlib

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, INVESTIGATOR, require_roles
from app.config import settings
from app.core import layer1_visual as l1
from app.core.audit_ledger import Signer, append_event, get_signer
from app.core.layer2_semantic import demo_template, extract_scores
from app.core.payload import PayloadDecodeError, decode_scores
from app.core.vision_extractor import decode_photo
from app.db import get_session
from app.db.models import Copy, User
from app.models.registry_models import (
    Attribution,
    IntakeResult,
    IntakeTextRequest,
    LedgerRef,
)

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])
_investigator = require_roles(ADMIN, INVESTIGATOR)

NOTES = {
    "IDENTIFIED": "Atribusi menunjukkan salinan yang diterbitkan, bukan putusan bersalah.",
    "UNREGISTERED": "Payload terbaca tetapi tidak terdaftar: tidak ada atribusi.",
    "INSUFFICIENT_FORENSIC_ARTIFACTS": "Bukti tidak cukup; sistem menolak menebak.",
}
PHOTO_DPI = 300
MAX_PHOTO_SIDE = 4000  # foto lebih besar diperkecil dulu: tak menambah akurasi, hanya waktu
PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _attribute(
    session: Session,
    signer: Signer,
    user: User,
    event: str,
    decoded: tuple[int, int] | None,
    evidence: bytes,
    observed: int,
    total: int,
    case_ref: str | None,
) -> IntakeResult:
    """Petakan hasil dekode ke salinan terdaftar dan catat pemeriksaan di ledger.

    Dua pagar anti salah-tuduh: dekoder menolak bukti rusak berat, dan `copy_id` hasil dekode
    wajib terdaftar. Setiap pemeriksaan (termasuk yang ditolak) dicatat; yang disimpan hanya
    hash bukti, bukan isinya."""
    copy_id = decoded[0] if decoded else None
    copy = session.get(Copy, copy_id) if copy_id is not None else None
    if copy is not None:
        status = "IDENTIFIED"
    else:
        status = "UNREGISTERED" if decoded else "INSUFFICIENT_FORENSIC_ARTIFACTS"
    entry = append_event(
        session,
        signer,
        event,
        {
            "evidence_sha256": hashlib.sha256(evidence).hexdigest(),
            "status": status,
            "copy_id": copy_id,
            "observed_bits": observed,
            "total_bits": total,
            "case_ref": case_ref,
        },
        user.username,
    )
    session.commit()

    attribution = None
    if copy is not None:
        attribution = Attribution(
            copy_id=copy.copy_id,
            recipient=copy.recipient,
            document_nomor=copy.document.nomor,
            document_judul=copy.document.judul,
            klasifikasi=copy.document.klasifikasi,
            issued_at=copy.issued_at,
        )
    return IntakeResult(
        status=status,
        observed_bits=observed,
        total_bits=total,
        attribution=attribution,
        ledger=LedgerRef(seq=entry.seq, entry_hash=entry.entry_hash),
        note=NOTES[status],
    )


@router.post("/text", response_model=IntakeResult)
def intake_text(
    body: IntakeTextRequest,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_investigator),
) -> IntakeResult:
    """Analisis teks bukti (ketik ulang / salinan teks) lewat Lapis 2."""
    template = demo_template()
    scores = extract_scores(template, body.text)
    try:
        decoded = decode_scores(scores)
    except PayloadDecodeError:
        decoded = None
    return _attribute(
        session, signer, user, "LEAK_INTAKE_TEXT", decoded, body.text.encode("utf-8"),
        len(scores), template.capacity_bits, body.case_ref,
    )


def _read_photo(data: bytes) -> np.ndarray:
    gray = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise HTTPException(422, "Berkas bukan gambar yang bisa dibaca (JPEG/PNG/WebP).")
    side = max(gray.shape)
    if side > MAX_PHOTO_SIDE:
        f = MAX_PHOTO_SIDE / side
        gray = cv2.resize(gray, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    return gray


def _preview(aligned: np.ndarray) -> str:
    small = cv2.resize(aligned, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return base64.b64encode(buf.tobytes()).decode("ascii") if ok else ""


@router.post("/photo", response_model=IntakeResult)
def intake_photo(
    photo: UploadFile = File(description="Foto/scan halaman naskah (JPEG, PNG, atau WebP)"),
    case_ref: str | None = Form(default=None, max_length=64),
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_investigator),
) -> IntakeResult:
    """Analisis foto halaman naskah lewat Lapis 1 (pergeseran spasi antar-kata).

    Seluruh halaman sebaiknya terlihat. Prosesnya beberapa detik; foto yang ditolak lebih lama
    karena semua kandidat pelurusan dicoba."""
    if photo.content_type not in PHOTO_TYPES:
        raise HTTPException(415, "Format foto harus JPEG, PNG, atau WebP.")
    limit = settings.max_photo_mb * 1024 * 1024
    data = photo.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"Foto lebih dari {settings.max_photo_mb} MB.")
    layout = l1.naskah_layout()
    found = decode_photo(_read_photo(data), layout, settings.layer1_delta_pt, PHOTO_DPI)
    result = _attribute(
        session, signer, user, "LEAK_INTAKE_PHOTO", found.decoded if found else None, data,
        len(found.scores) if found else 0, layout.total_slots, case_ref,
    )
    if found is not None:
        result.aligned_preview = _preview(found.aligned)
    return result
