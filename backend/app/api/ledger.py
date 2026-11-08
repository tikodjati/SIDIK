from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, INVESTIGATOR, require_roles
from app.core.audit_ledger import Signer, get_signer, verify_chain
from app.db import get_session
from app.db.models import LedgerEntry
from app.models.registry_models import LedgerEntryOut, VerifyOut

# Ledger memuat riwayat investigasi, jadi distributor tidak boleh membacanya.
router = APIRouter(
    prefix="/api/v1/ledger",
    tags=["ledger"],
    dependencies=[Depends(require_roles(ADMIN, INVESTIGATOR))],
)


@router.get("", response_model=list[LedgerEntryOut])
def list_entries(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    newest_first: bool = False,
    session: Session = Depends(get_session),
) -> list[LedgerEntry]:
    order = LedgerEntry.seq.desc() if newest_first else LedgerEntry.seq
    return list(session.scalars(select(LedgerEntry).order_by(order).offset(offset).limit(limit)))


@router.get("/verify", response_model=VerifyOut)
def verify(
    session: Session = Depends(get_session), signer: Signer = Depends(get_signer)
) -> VerifyOut:
    """Verifikasi seluruh rantai (hash, urutan, tanda tangan). Catat `head_hash` secara berkala
    di luar sistem untuk mendeteksi pemotongan ekor rantai."""
    result = verify_chain(session, {signer.key_id: signer.public_key})
    return VerifyOut(**result.__dict__)
