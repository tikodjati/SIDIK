"""Lapis 4: data personel demo (pengganti SISFO), ekspor bersisip honey-record, dan korpus data
publik untuk pemeriksa klaim dump."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, DISTRIBUTOR, INVESTIGATOR, require_roles
from app.config import settings
from app.core import layer4_store as store
from app.core.audit_ledger import Signer, append_event, get_signer
from app.db import get_session
from app.db.models import DataExport, Personnel, PublicCorpus, User
from app.models.personnel_models import (
    CorpusOut,
    ExportOut,
    ExportRequest,
    PersonnelSummary,
    SatuanCount,
    SeedResult,
)

router = APIRouter(prefix="/api/v1", tags=["personnel"])
_staff = require_roles(ADMIN, DISTRIBUTOR)
_admin = require_roles(ADMIN)


def read_upload(upload: UploadFile) -> bytes:
    limit = settings.max_dump_mb * 1024 * 1024
    data = upload.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"Berkas lebih dari {settings.max_dump_mb} MB.")
    return data


@router.get(
    "/personnel/summary", response_model=PersonnelSummary, dependencies=[Depends(_staff)]
)
def personnel_summary(session: Session = Depends(get_session)) -> PersonnelSummary:
    rows = session.execute(
        select(Personnel.satuan, func.count()).group_by(Personnel.satuan).order_by(Personnel.satuan)
    ).all()
    return PersonnelSummary(
        total=sum(n for _, n in rows),
        by_satuan=[SatuanCount(satuan=s, count=n) for s, n in rows],
    )


@router.post("/personnel/seed-demo", response_model=SeedResult, status_code=201)
def seed_demo(
    count: int = 400,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_admin),
) -> SeedResult:
    """Isi data personel demo (rekaan) beserta honey-record tertanam. Sekali saja; ditolak bila
    data personel sudah ada."""
    if not 50 <= count <= 5000:
        raise HTTPException(422, "Jumlah baris harus 50-5000.")
    try:
        rows, sentinels = store.seed_personnel(session, count)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    append_event(session, signer, "PERSONNEL_SEEDED", {"rows": rows}, user.username)
    session.commit()
    return SeedResult(rows=rows, honey_records=sentinels)


@router.post(
    "/personnel/exports",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_personnel(
    body: ExportRequest,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_staff),
) -> Response:
    """Ekspor data personel ke CSV. Setiap ekspor diberi honey-record uniknya sendiri dan dicatat
    di ledger (akun, satuan, keperluan), sehingga dump yang bocor dapat ditelusuri ke ekspor ini."""
    try:
        export, text = store.create_export(
            session, user.username, body.satuan or None, body.purpose
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    append_event(
        session,
        signer,
        "DATA_EXPORTED",
        {
            "export_id": export.id,
            "satuan": export.satuan,
            "rows": export.row_count,
            "purpose": export.purpose,
        },
        user.username,
    )
    session.commit()
    name = f"personel_{export.id:05d}.csv"
    return Response(
        text.encode("utf-8"),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "X-Export-Id": str(export.id),
        },
    )


@router.get(
    "/personnel/exports",
    response_model=list[ExportOut],
    dependencies=[Depends(require_roles(ADMIN, DISTRIBUTOR, INVESTIGATOR))],
)
def list_exports(session: Session = Depends(get_session)) -> list[DataExport]:
    return list(session.scalars(select(DataExport).order_by(DataExport.id.desc())))


@router.post("/corpora", response_model=CorpusOut, status_code=201)
def register_corpus(
    file: UploadFile = File(description="Data publik/bocoran lama yang sudah dikenal"),
    label: str = Form(min_length=3, max_length=128),
    note: str = Form(default="", max_length=256),
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_admin),
) -> PublicCorpus:
    """Daftarkan korpus data publik lama untuk mendeteksi dump daur ulang. Hanya hash NIK dan
    nomor HP yang disimpan; isi berkas dibuang."""
    text = read_upload(file).decode("utf-8", errors="replace")
    try:
        corpus = store.register_corpus(session, label, note, text)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, f"Korpus '{label}' sudah terdaftar") from exc
    append_event(
        session, signer, "CORPUS_REGISTERED",
        {"corpus_id": corpus.id, "label": label, "entries": corpus.entries}, user.username,
    )
    session.commit()
    return corpus


@router.get(
    "/corpora",
    response_model=list[CorpusOut],
    dependencies=[Depends(require_roles(ADMIN, INVESTIGATOR))],
)
def list_corpora(session: Session = Depends(get_session)) -> list[PublicCorpus]:
    return list(session.scalars(select(PublicCorpus).order_by(PublicCorpus.id)))
