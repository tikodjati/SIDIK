import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, DISTRIBUTOR, require_roles
from app.config import settings
from app.core import layer1_visual as l1
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
)

router = APIRouter(prefix="/api/v1", tags=["registry"])

_staff = require_roles(ADMIN, DISTRIBUTOR)


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
    return [
        CopyOut(
            copy_id=c.copy_id,
            document_id=c.document_id,
            document_nomor=c.document.nomor,
            recipient_id=c.recipient_id,
            recipient_nama=c.recipient.nama,
            recipient_nrp=c.recipient.nrp,
            issued_at=c.issued_at,
        )
        for c in rows
    ]


@router.get(
    "/copies/{copy_id}/text",
    response_model=CopyText,
    dependencies=[Depends(require_roles(ADMIN))],
)
def copy_text(copy_id: int, session: Session = Depends(get_session)) -> CopyText:
    """Render ulang teks salinan (deterministik) untuk simulasi demo kebocoran. Hanya admin."""
    if session.get(Copy, copy_id) is None:
        raise HTTPException(404, "salinan tidak ditemukan")
    return CopyText(copy_id=copy_id, text=encode_text(demo_template(), encode_payload(copy_id)))


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
    """PDF salinan untuk dicetak: naskah dinas dengan penanda Lapis 1 (spasi antar-kata).
    Teksnya sama untuk semua salinan; identitas hanya ada di spasinya. Setiap unduhan dicatat."""
    copy = session.get(Copy, copy_id)
    if copy is None:
        raise HTTPException(404, "salinan tidak ditemukan")
    pdf = l1.render_pdf(l1.naskah_layout(), encode_payload(copy_id), settings.layer1_delta_pt)
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
    """Terbitkan satu salinan bertanda untuk satu penerima dan catat di buku besar audit."""
    document = session.get(Document, document_id)
    recipient = session.get(Recipient, body.recipient_id)
    if document is None or recipient is None:
        raise HTTPException(404, "naskah atau penerima tidak ditemukan")
    exists = session.scalars(
        select(Copy).where(Copy.document_id == document_id, Copy.recipient_id == recipient.id)
    ).first()
    if exists:
        raise HTTPException(409, "salinan untuk penerima ini sudah diterbitkan")

    copy_id = secrets.randbits(32)
    while copy_id == 0 or session.get(Copy, copy_id) is not None:
        copy_id = secrets.randbits(32)  # acak, bukan berurutan: tak bisa ditebak
    copy = Copy(copy_id=copy_id, document_id=document.id, recipient_id=recipient.id)
    session.add(copy)
    session.flush()
    entry = append_event(
        session,
        signer,
        "COPY_ISSUED",
        {
            "copy_id": copy_id,
            "document_nomor": document.nomor,
            "recipient_nrp": recipient.nrp,
            "klasifikasi": document.klasifikasi,
        },
        user.username,
    )
    session.commit()
    text = encode_text(demo_template(), encode_payload(copy_id))
    return CopyIssued(
        copy_id=copy_id,
        document_id=document.id,
        recipient_id=recipient.id,
        issued_at=copy.issued_at,
        text=text,
        ledger_seq=entry.seq,
    )
