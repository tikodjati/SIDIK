import base64
import hashlib

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, INVESTIGATOR, require_roles
from app.api.personnel import read_upload
from app.config import settings
from app.core import layer3_honeytoken as l3
from app.core import layer4_store, naskah
from app.core.audit_ledger import Signer, append_event, get_signer
from app.core.layer2_semantic import demo_template, extract_scores, official_similarity
from app.core.payload import PayloadDecodeError, decode_scores
from app.db import get_session
from app.db.models import Copy, DataExport, User
from app.models.personnel_models import DumpResult, DumpSource, ExportOut, IdentifierCounts
from app.models.registry_models import (
    Attribution,
    IntakeResult,
    IntakeTextRequest,
    LayerReading,
    LedgerRef,
    TokenHit,
)

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])
_investigator = require_roles(ADMIN, INVESTIGATOR)

NOTES = {
    "IDENTIFIED": "Atribusi menunjukkan salinan yang diterbitkan, bukan putusan bersalah.",
    "COLLUSION_SUSPECTED": "Bukti menunjuk lebih dari satu salinan, masing-masing dengan bukti "
    "cukup (indikasi kolusi/penggabungan salinan). Atribusi menunjukkan salinan yang diterbitkan, "
    "bukan putusan bersalah.",
    "UNREGISTERED": "Payload terbaca tetapi tidak terdaftar: tidak ada atribusi.",
    "CONFLICTING_EVIDENCE": "Lapis 1 dan Lapis 2 menunjuk salinan berbeda (indikasi manipulasi): "
    "tidak ada atribusi.",
    "INSUFFICIENT_FORENSIC_ARTIFACTS": "Bukti tidak cukup; sistem menolak menebak.",
}
PHOTO_DPI = 300
MAX_PHOTO_SIDE = 4000  # foto lebih besar diperkecil dulu: tak menambah akurasi, hanya waktu
PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _attribution(copy: Copy) -> Attribution:
    return Attribution(
        copy_id=copy.copy_id,
        recipient=copy.recipient,
        document_nomor=copy.document.nomor,
        document_judul=copy.document.judul,
        klasifikasi=copy.document.klasifikasi,
        issued_at=copy.issued_at,
    )


def _token_layer(hits: list[l3.TokenHit]) -> LayerReading:
    found = {(h.copy_id, h.token_index) for h in hits}
    return LayerReading(
        layer="L3_TOKEN",
        observed_bits=len(found),
        total_bits=len(demo_template().tokens),
        decoded_alone=bool(l3.judge(hits, None).identified),
    )


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
    layers: list[LayerReading] | None = None,
    conflict: bool = False,
    hits: list[l3.TokenHit] | None = None,
) -> IntakeResult:
    """Petakan hasil dekode Lapis 1/2 dan honey-token Lapis 3 ke salinan terdaftar, lalu catat
    pemeriksaan di ledger.

    Pagar anti salah-tuduh: dekoder menolak bukti rusak berat, `copy_id` hasil dekode wajib
    terdaftar, dan honey-token baru menunjuk salinan bila >= 2 tokennya cocok (atau dikonfirmasi
    lapis lain). Salinan yang belum pernah diedarkan (menunggu persetujuan / ditolak) tidak
    diatribusikan: penerimanya tak pernah memegangnya. Setiap pemeriksaan (termasuk yang
    ditolak) dicatat; yang disimpan hanya hash bukti, bukan isinya."""

    def released(c: Copy | None) -> bool:
        return c is not None and (c.status or "ISSUED") == "ISSUED"

    hits = [h for h in hits or [] if released(session.get(Copy, h.copy_id))]
    copy_id = decoded[0] if decoded else None
    decoded_copy = session.get(Copy, copy_id) if copy_id is not None else None
    decoded_copy = decoded_copy if released(decoded_copy) else None
    verdict = l3.judge(hits, decoded_copy.copy_id if decoded_copy else None)
    copies = [session.get(Copy, c) for c in verdict.identified]
    if conflict:
        status, copies = "CONFLICTING_EVIDENCE", []
    elif len(copies) > 1:
        status = "COLLUSION_SUSPECTED"
    elif copies:
        status = "IDENTIFIED"
    else:
        status = "UNREGISTERED" if decoded else "INSUFFICIENT_FORENSIC_ARTIFACTS"
    attributed = {c.copy_id for c in copies}
    entry = append_event(
        session,
        signer,
        event,
        {
            "evidence_sha256": hashlib.sha256(evidence).hexdigest(),
            "status": status,
            "copy_id": copies[0].copy_id if len(copies) == 1 else copy_id,
            "observed_bits": observed,
            "total_bits": total,
            "case_ref": case_ref,
            **({"layers": [r.model_dump() for r in layers]} if layers else {}),
            **({"copy_ids": sorted(attributed)} if len(copies) > 1 else {}),
            **(
                {"tokens": [{"index": h.token_index, "copy_id": h.copy_id} for h in hits]}
                if hits else {}
            ),
        },
        user.username,
    )
    session.commit()

    token_hits = []
    for h in hits:
        owner = session.get(Copy, h.copy_id)
        token_hits.append(TokenHit(
            token_index=h.token_index,
            value=h.value,
            copy_id=h.copy_id,
            recipient_nama=owner.recipient.nama,
            recipient_nrp=owner.recipient.nrp,
            confirmed=h.copy_id in attributed,
        ))
    attributions = [_attribution(c) for c in copies]
    return IntakeResult(
        status=status,
        observed_bits=observed,
        total_bits=total,
        layers=layers or [],
        attribution=attributions[0] if status == "IDENTIFIED" else None,
        attributions=attributions,
        tokens=token_hits,
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
    """Analisis teks bukti (ketik ulang / salinan teks / parafrase) lewat Lapis 2 (pilihan kata)
    dan Lapis 3 (honey-token: angka fiktif khusus salinan)."""
    template = demo_template()
    scores = extract_scores(template, body.text)
    try:
        decoded = decode_scores(scores)
    except PayloadDecodeError:
        decoded = None
    hits = l3.lookup(session, l3.numbers_in(body.text))
    layers = [
        LayerReading(
            layer="L2_KATA",
            observed_bits=len(scores),
            total_bits=template.capacity_bits,
            decoded_alone=decoded is not None,
        ),
        _token_layer(hits),
    ]
    result = _attribute(
        session, signer, user, "LEAK_INTAKE_TEXT", decoded, body.text.encode("utf-8"),
        len(scores), template.capacity_bits, body.case_ref, layers=layers, hits=hits,
    )
    result.official_similarity = official_similarity(template, body.text)
    return result


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
    """Analisis foto halaman PDF salinan: pilihan kata (Lapis 2) dan angka honey-token (Lapis 3)
    dibaca dari bentuknya, lalu pergeseran spasi (Lapis 1) diukur; bukti Lapis 1 dan 2 digabung.
    Bila keduanya menunjuk salinan berbeda, hasilnya CONFLICTING_EVIDENCE.

    Seluruh halaman sebaiknya terlihat. Prosesnya beberapa detik; foto yang ditolak lebih lama
    karena semua kandidat pelurusan dicoba."""
    if photo.content_type not in PHOTO_TYPES:
        raise HTTPException(415, "Format foto harus JPEG, PNG, atau WebP.")
    limit = settings.max_photo_mb * 1024 * 1024
    data = photo.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"Foto lebih dari {settings.max_photo_mb} MB.")
    found = naskah.decode_naskah_photo(_read_photo(data), settings.layer1_delta_pt, PHOTO_DPI)
    l1_total = naskah.generic_layout().total_slots
    l2_total = demo_template().capacity_bits
    layers = [
        LayerReading(
            layer="L1_SPASI",
            observed_bits=len(found.layer1_scores) if found else 0,
            total_bits=l1_total,
            decoded_alone=bool(found and found.layer1_decoded),
        ),
        LayerReading(
            layer="L2_KATA",
            observed_bits=len(found.layer2_scores) if found else 0,
            total_bits=l2_total,
            decoded_alone=bool(found and found.layer2_decoded),
        ),
    ]
    hits = l3.lookup(session, (l3.digits_of(v) for v in found.tokens.values())) if found else []
    layers.append(_token_layer(hits))
    result = _attribute(
        session, signer, user, "LEAK_INTAKE_PHOTO", found.decoded if found else None, data,
        found.observed if found else 0, l1_total + l2_total, case_ref,
        layers=layers, conflict=bool(found and found.conflict), hits=hits,
    )
    if found is not None:
        result.aligned_preview = _preview(found.aligned)
    return result


DUMP_NOTES = {
    "AUTHENTIC_LEAK": "Dump memuat honey-record: data benar berasal dari basis data kita. Sumber "
    "menunjukkan ekspor/akses yang bocor, bukan putusan bersalah.",
    "UNTRACED_MATCH": "Identitas cocok dengan data personel kita, tetapi honey-record tidak cukup: "
    "kemungkinan data asli dari sumber tak terlacak (mis. potongan kecil). Tidak ada atribusi.",
    "RECYCLED_PUBLIC": "Sebagian besar identitas berasal dari data publik/bocoran lama yang sudah "
    "dikenal: indikasi daur ulang (psywar/hoaks), bukan kebocoran basis data kita.",
    "FABRICATED": "Banyak NIK berformat tidak valid: indikasi data rekaan (psywar/hoaks).",
    "NOT_FROM_OUR_DB": "Identitas tidak cocok dengan data personel kita: tidak terbukti berasal "
    "dari basis data ini.",
    "INSUFFICIENT_DATA": "Tidak ditemukan NIK, nomor HP, atau NRP di berkas.",
}


@router.post("/dump", response_model=DumpResult)
def intake_dump(
    file: UploadFile = File(description="Data dump yang beredar (CSV, SQL, JSON, atau teks)"),
    case_ref: str | None = Form(default=None, max_length=64),
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_investigator),
) -> DumpResult:
    """Periksa klaim kebocoran basis data (Lapis 4): cari honey-record (bukti pasti dan sumber
    ekspornya), lalu bandingkan identitas dengan data personel dan korpus data publik lama untuk
    membedakan kebocoran asli dari daur ulang atau rekaan."""
    data = read_upload(file)
    report = layer4_store.analyse_dump(session, data.decode("utf-8", errors="replace"))
    proven = set(report.proven)
    counts: dict[int | None, int] = {}
    for hit in report.hits:
        counts[hit.source] = counts.get(hit.source, 0) + 1
    sources = [
        DumpSource(
            export=ExportOut.model_validate(session.get(DataExport, s)) if s is not None else None,
            matched_rows=n,
            proven=s in proven,
        )
        for s, n in sorted(counts.items(), key=lambda kv: (kv[0] not in proven, kv[0] is None))
    ]
    entry = append_event(
        session,
        signer,
        "LEAK_INTAKE_DUMP",
        {
            "evidence_sha256": hashlib.sha256(data).hexdigest(),
            "status": report.status,
            "export_ids": [s for s in report.proven if s is not None],
            "db_direct": None in proven,
            "honey_rows": len(report.hits),
            "identifiers": report.ids.total,
            "personnel_ratio": round(report.personnel_ratio, 3),
            "corpus_ratio": round(report.corpus_ratio, 3),
            "case_ref": case_ref,
        },
        user.username,
    )
    session.commit()
    return DumpResult(
        status=report.status,
        identifiers=IdentifierCounts(
            nik=len(report.ids.niks), no_hp=len(report.ids.phones), nrp=len(report.ids.nrps)
        ),
        personnel_ratio=report.personnel_ratio,
        corpus_ratio=report.corpus_ratio,
        corpus_label=report.corpus_label,
        invalid_ratio=report.invalid_ratio,
        sources=sources,
        ledger=LedgerRef(seq=entry.seq, entry_hash=entry.entry_hash),
        note=DUMP_NOTES[report.status],
    )
