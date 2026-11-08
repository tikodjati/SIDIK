import hashlib

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, INVESTIGATOR, require_roles
from app.core.audit_ledger import Signer, append_event, get_signer
from app.core.layer2_semantic import demo_template, extract_scores
from app.core.payload import PayloadDecodeError, decode_scores
from app.db import get_session
from app.db.models import Copy, User
from app.models.registry_models import Attribution, IntakeResult, IntakeTextRequest, LedgerRef

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])
_investigator = require_roles(ADMIN, INVESTIGATOR)

NOTES = {
    "IDENTIFIED": "Atribusi menunjukkan salinan yang diterbitkan, bukan putusan bersalah.",
    "UNREGISTERED": "Payload terbaca tetapi tidak terdaftar: tidak ada atribusi.",
    "INSUFFICIENT_FORENSIC_ARTIFACTS": "Bukti tidak cukup; sistem menolak menebak.",
}


@router.post("/text", response_model=IntakeResult)
def intake_text(
    body: IntakeTextRequest,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_investigator),
) -> IntakeResult:
    """Analisis teks bukti, petakan ke salinan terdaftar, dan catat investigasi di ledger.

    Dua pagar anti salah-tuduh: dekoder menolak bukti rusak berat, dan `copy_id` hasil dekode
    wajib terdaftar. Setiap pemeriksaan (termasuk yang ditolak) dicatat; yang disimpan hanya
    hash bukti, bukan isi teksnya."""
    template = demo_template()
    scores = extract_scores(template, body.text)
    status = "INSUFFICIENT_FORENSIC_ARTIFACTS"
    copy: Copy | None = None
    copy_id: int | None = None
    try:
        copy_id, _ = decode_scores(scores)
    except PayloadDecodeError:
        pass
    else:
        copy = session.get(Copy, copy_id)
        status = "IDENTIFIED" if copy else "UNREGISTERED"

    entry = append_event(
        session,
        signer,
        "LEAK_INTAKE_TEXT",
        {
            "evidence_sha256": hashlib.sha256(body.text.encode("utf-8")).hexdigest(),
            "status": status,
            "copy_id": copy_id,
            "observed_bits": len(scores),
            "total_bits": template.capacity_bits,
            "case_ref": body.case_ref,
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
        observed_bits=len(scores),
        total_bits=template.capacity_bits,
        attribution=attribution,
        ledger=LedgerRef(seq=entry.seq, entry_hash=entry.entry_hash),
        note=NOTES[status],
    )
