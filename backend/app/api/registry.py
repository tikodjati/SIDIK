import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit_ledger import Signer, append_event, get_signer
from app.core.layer2_semantic import demo_template, encode_text
from app.core.payload import encode_payload
from app.db import get_session
from app.db.models import Copy, Document, Recipient
from app.models.registry_models import (
    CopyIssued,
    CopyRequest,
    DocumentIn,
    DocumentOut,
    RecipientIn,
    RecipientOut,
)

router = APIRouter(prefix="/api/v1", tags=["registry"])


@router.post("/recipients", response_model=RecipientOut, status_code=201)
def create_recipient(body: RecipientIn, session: Session = Depends(get_session)) -> Recipient:
    recipient = Recipient(**body.model_dump())
    session.add(recipient)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, f"NRP {body.nrp} sudah terdaftar") from exc
    return recipient


@router.get("/recipients", response_model=list[RecipientOut])
def list_recipients(session: Session = Depends(get_session)) -> list[Recipient]:
    return list(session.scalars(select(Recipient).order_by(Recipient.id)))


@router.post("/documents", response_model=DocumentOut, status_code=201)
def create_document(body: DocumentIn, session: Session = Depends(get_session)) -> Document:
    document = Document(**body.model_dump())
    session.add(document)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, f"Nomor naskah {body.nomor} sudah terdaftar") from exc
    return document


@router.post("/documents/{document_id}/copies", response_model=CopyIssued, status_code=201)
def issue_copy(
    document_id: int,
    body: CopyRequest,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    actor: str = Header(default="anonim", alias="X-Actor"),
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
        actor,
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
