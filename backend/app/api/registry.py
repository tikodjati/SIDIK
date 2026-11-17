import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, DISTRIBUTOR, require_roles
from app.config import settings
from app.core import layer3_honeytoken as l3
from app.core import naskah
from app.core.audit_ledger import Signer, append_event, get_signer
from app.core.layer2_semantic import demo_template, encode_text
from app.core.payload import encode_payload
from app.db import get_session
from app.db.models import Copy, Document, Recipient, User
from app.models.registry_models import (
    CopyIssued,
    CopyOut,
    CopyRequest,
    CopyText,
    DocumentIn,
    DocumentOut,
    RecipientIn,
    RecipientOut,
    RejectRequest,
)

router = APIRouter(prefix="/api/v1", tags=["registry"])

_staff = require_roles(ADMIN, DISTRIBUTOR)
_admin = require_roles(ADMIN)

# Four-eyes principle: salinan naskah berklasifikasi ini baru terbit setelah disetujui admin lain.
NEEDS_APPROVAL = {"RAHASIA", "SANGAT RAHASIA"}


def _copy_out(c: Copy) -> CopyOut:
    return CopyOut(
        copy_id=c.copy_id,
        document_id=c.document_id,
        document_nomor=c.document.nomor,
        recipient_id=c.recipient_id,
        recipient_nama=c.recipient.nama,
        recipient_nrp=c.recipient.nrp,
        klasifikasi=c.document.klasifikasi,
        issued_at=c.issued_at,
        status=c.status or "ISSUED",
        requested_by=c.requested_by,
        approved_by=c.approved_by,
    )


def _released(session: Session, copy_id: int) -> Copy:
    """Salinan yang sudah terbit; salinan yang menunggu persetujuan/ditolak tak boleh keluar."""
    copy = session.get(Copy, copy_id)
    if copy is None:
        raise HTTPException(404, "salinan tidak ditemukan")
    if (copy.status or "ISSUED") != "ISSUED":
        raise HTTPException(409, "Salinan belum disetujui (menunggu persetujuan atau ditolak).")
    return copy


@router.post(
    "/recipients", response_model=RecipientOut, status_code=201, dependencies=[Depends(_staff)]
)
def create_recipient(body: RecipientIn, session: Session = Depends(get_session)) -> Recipient:
    recipient = Recipient(**body.model_dump())
    session.add(recipient)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, f"NRP {body.nrp} sudah terdaftar") from exc
    return recipient


@router.get("/recipients", response_model=list[RecipientOut], dependencies=[Depends(_staff)])
def list_recipients(session: Session = Depends(get_session)) -> list[Recipient]:
    return list(session.scalars(select(Recipient).order_by(Recipient.id)))


@router.post(
    "/documents", response_model=DocumentOut, status_code=201, dependencies=[Depends(_staff)]
)
def create_document(body: DocumentIn, session: Session = Depends(get_session)) -> Document:
    document = Document(**body.model_dump())
    session.add(document)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, f"Nomor naskah {body.nomor} sudah terdaftar") from exc
    return document


@router.get("/documents", response_model=list[DocumentOut], dependencies=[Depends(_staff)])
def list_documents(session: Session = Depends(get_session)) -> list[Document]:
    return list(session.scalars(select(Document).order_by(Document.id)))


@router.get("/copies", response_model=list[CopyOut], dependencies=[Depends(_staff)])
def list_copies(session: Session = Depends(get_session)) -> list[CopyOut]:
    rows = session.scalars(select(Copy).order_by(Copy.issued_at.desc(), Copy.copy_id))
    return [_copy_out(c) for c in rows]


@router.get(
    "/copies/{copy_id}/text",
    response_model=CopyText,
    dependencies=[Depends(require_roles(ADMIN))],
)
def copy_text(copy_id: int, session: Session = Depends(get_session)) -> CopyText:
    """Render ulang teks salinan untuk simulasi demo kebocoran. Hanya admin."""
    copy = _released(session, copy_id)
    tokens = l3.ensure_tokens(session, copy, demo_template())
    session.commit()
    text = encode_text(demo_template(), encode_payload(copy_id), tokens)
    return CopyText(copy_id=copy_id, text=text)


@router.get(
    "/copies/{copy_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def copy_pdf(
    copy_id: int,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_staff),
) -> Response:
    """PDF salinan untuk dicetak: naskah dinas dengan pilihan kata khusus penerima (Lapis 2),
    pergeseran spasi antar-kata (Lapis 1), dan angka honey-token khusus salinan (Lapis 3).
    Pemenggalan baris sama untuk semua salinan. Setiap unduhan dicatat."""
    copy = _released(session, copy_id)
    tokens = l3.ensure_tokens(session, copy, demo_template())
    pdf = naskah.copy_pdf(copy_id, settings.layer1_delta_pt, tokens)
    data = {"copy_id": copy_id, "document_nomor": copy.document.nomor, "format": "pdf"}
    append_event(session, signer, "COPY_EXPORTED", data, user.username)
    session.commit()
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="salinan_{copy_id:08X}.pdf"'},
    )


@router.post("/documents/{document_id}/copies", response_model=CopyIssued, status_code=201)
def issue_copy(
    document_id: int,
    body: CopyRequest,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_staff),
) -> CopyIssued:
    """Terbitkan satu salinan bertanda untuk satu penerima dan catat di buku besar audit.

    Naskah RAHASIA/SANGAT RAHASIA: salinan berstatus PENDING (belum bisa diunduh) sampai disetujui
    admin lain (four-eyes principle). Pengajuan ulang setelah ditolak diperbolehkan."""
    document = session.get(Document, document_id)
    recipient = session.get(Recipient, body.recipient_id)
    if document is None or recipient is None:
        raise HTTPException(404, "naskah atau penerima tidak ditemukan")
    pending = document.klasifikasi in NEEDS_APPROVAL
    copy = session.scalars(
        select(Copy).where(Copy.document_id == document_id, Copy.recipient_id == recipient.id)
    ).first()
    if copy is not None and copy.status != "REJECTED":
        raise HTTPException(409, "salinan untuk penerima ini sudah diterbitkan atau diajukan")

    if copy is None:
        copy_id = secrets.randbits(32)
        while copy_id == 0 or session.get(Copy, copy_id) is not None:
            copy_id = secrets.randbits(32)  # acak, bukan berurutan: tak bisa ditebak
        copy = Copy(copy_id=copy_id, document_id=document.id, recipient_id=recipient.id)
        session.add(copy)
    copy.status = "PENDING" if pending else "ISSUED"
    copy.requested_by = user.username
    copy.approved_by = None
    copy.approved_at = None
    copy.issued_at = datetime.now(UTC)
    session.flush()
    tokens = l3.ensure_tokens(session, copy, demo_template())
    entry = append_event(
        session,
        signer,
        "COPY_REQUESTED" if pending else "COPY_ISSUED",
        {
            "copy_id": copy.copy_id,
            "document_nomor": document.nomor,
            "recipient_nrp": recipient.nrp,
            "klasifikasi": document.klasifikasi,
        },
        user.username,
    )
    session.commit()
    text = None if pending else encode_text(demo_template(), encode_payload(copy.copy_id), tokens)
    return CopyIssued(
        copy_id=copy.copy_id,
        document_id=document.id,
        recipient_id=recipient.id,
        issued_at=copy.issued_at,
        status=copy.status,
        text=text,
        ledger_seq=entry.seq,
    )


def _pending(session: Session, copy_id: int) -> Copy:
    copy = session.get(Copy, copy_id)
    if copy is None:
        raise HTTPException(404, "salinan tidak ditemukan")
    if copy.status != "PENDING":
        raise HTTPException(409, "Salinan tidak sedang menunggu persetujuan.")
    return copy


@router.post("/copies/{copy_id}/approve", response_model=CopyOut)
def approve_copy(
    copy_id: int,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_admin),
) -> CopyOut:
    """Setujui salinan naskah RAHASIA/SANGAT RAHASIA. Wajib admin selain pengaju (four-eyes)."""
    copy = _pending(session, copy_id)
    if copy.requested_by == user.username:
        raise HTTPException(403, "Persetujuan harus oleh pejabat lain, bukan pengaju (four-eyes).")
    copy.status = "ISSUED"
    copy.approved_by = user.username
    copy.approved_at = copy.issued_at = datetime.now(UTC)
    append_event(
        session,
        signer,
        "COPY_APPROVED",
        {
            "copy_id": copy.copy_id,
            "document_nomor": copy.document.nomor,
            "recipient_nrp": copy.recipient.nrp,
            "requested_by": copy.requested_by,
        },
        user.username,
    )
    session.commit()
    return _copy_out(copy)


@router.post("/copies/{copy_id}/reject", response_model=CopyOut)
def reject_copy(
    copy_id: int,
    body: RejectRequest,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_admin),
) -> CopyOut:
    """Tolak pengajuan salinan; salinan tak pernah bisa diunduh. Alasan dicatat di ledger."""
    copy = _pending(session, copy_id)
    copy.status = "REJECTED"
    append_event(
        session,
        signer,
        "COPY_REJECTED",
        {"copy_id": copy.copy_id, "requested_by": copy.requested_by, "reason": body.reason},
        user.username,
    )
    session.commit()
    return _copy_out(copy)
