from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import ADMIN, INVESTIGATOR, require_roles
from app.core.audit_ledger import Signer, append_event, get_signer
from app.db import get_session
from app.db.models import BeaconHit, Copy, User
from app.models.beacon_models import BeaconHitOut, BeaconSimulateIn

router = APIRouter(prefix="/api/v1", tags=["beacon"])

_investigators = require_roles(ADMIN, INVESTIGATOR)

# 1x1 transparent GIF bytes standard canary token
_TRANSPARENT_GIF_1X1 = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04"
    b"\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;"
)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


@router.get(
    "/beacon/hits",
    response_model=list[BeaconHitOut],
    dependencies=[Depends(_investigators)],
)
def list_beacon_hits(session: Session = Depends(get_session)) -> list[BeaconHitOut]:
    """Daftar seluruh pemicuan suar pelacak (Canary Beacon Hits) untuk radar investigasi."""
    stmt = (
        select(BeaconHit)
        .options(
            joinedload(BeaconHit.copy).joinedload(Copy.document),
            joinedload(BeaconHit.copy).joinedload(Copy.recipient),
        )
        .order_by(BeaconHit.detected_at.desc())
    )
    hits = session.scalars(stmt).all()

    results: list[BeaconHitOut] = []
    for h in hits:
        c = h.copy
        results.append(
            BeaconHitOut(
                id=h.id,
                copy_id=h.copy_id,
                ip_address=h.ip_address,
                user_agent=h.user_agent,
                referer=h.referer,
                detected_at=h.detected_at,
                document_nomor=c.document.nomor if c and c.document else None,
                recipient_nama=c.recipient.nama if c and c.recipient else None,
                recipient_nrp=c.recipient.nrp if c and c.recipient else None,
                klasifikasi=c.document.klasifikasi if c and c.document else None,
            )
        )
    return results


@router.post(
    "/beacon/{copy_id}/simulate",
    response_model=BeaconHitOut,
    dependencies=[Depends(_investigators)],
)
def simulate_beacon_hit(
    copy_id: int,
    body: BeaconSimulateIn,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
    user: User = Depends(_investigators),
) -> BeaconHitOut:
    """Simulasi pemicuan suar pelacak untuk pengujian dan demonstrasi investigasi."""
    copy = session.get(Copy, copy_id)
    if copy is None:
        raise HTTPException(404, "Salinan tidak ditemukan.")

    hit = BeaconHit(
        copy_id=copy.copy_id,
        ip_address=body.ip_address,
        user_agent=body.user_agent,
        referer=body.referer,
    )
    session.add(hit)

    append_event(
        session,
        signer,
        "BEACON_TRIGGERED",
        {
            "copy_id": copy.copy_id,
            "ip_address": body.ip_address,
            "user_agent": body.user_agent,
            "referer": body.referer,
            "document_nomor": copy.document.nomor if copy.document else None,
            "recipient_nrp": copy.recipient.nrp if copy.recipient else None,
            "recipient_nama": copy.recipient.nama if copy.recipient else None,
            "simulated_by": user.username,
        },
        user.username,
    )
    session.commit()
    session.refresh(hit)

    return BeaconHitOut(
        id=hit.id,
        copy_id=hit.copy_id,
        ip_address=hit.ip_address,
        user_agent=hit.user_agent,
        referer=hit.referer,
        detected_at=hit.detected_at,
        document_nomor=copy.document.nomor if copy.document else None,
        recipient_nama=copy.recipient.nama if copy.recipient else None,
        recipient_nrp=copy.recipient.nrp if copy.recipient else None,
        klasifikasi=copy.document.klasifikasi if copy.document else None,
    )


@router.get("/beacon/{copy_id}", response_class=Response)
def trigger_beacon(
    copy_id: int,
    request: Request,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
) -> Response:
    """Endpoint publik penerima suar (Canary Token Receiver).

    Dipicu secara otomatis oleh pembaca PDF eksternal ketika naskah dibuka.
    Mengekstrak alamat IP publik pembaca, User-Agent (identitas software/OS),
    mencatat ke pangkalan data dan mengunci ke dalam Buku Besar Audit (Ed25519).
    Mengembalikan 1x1 transparent GIF agar pembaca dokumen tidak menampilkan galat.
    """
    copy = session.get(Copy, copy_id)
    if copy is None:
        # Kembalikan response kosong stealthy agar peretas tidak tahu keberadaan endpoint
        return Response(content=_TRANSPARENT_GIF_1X1, media_type="image/gif")

    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    hit = BeaconHit(
        copy_id=copy.copy_id,
        ip_address=client_ip,
        user_agent=user_agent[:512] if user_agent else None,
        referer=referer[:256] if referer else None,
    )
    session.add(hit)

    append_event(
        session,
        signer,
        "BEACON_TRIGGERED",
        {
            "copy_id": copy.copy_id,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "referer": referer,
            "document_nomor": copy.document.nomor if copy.document else None,
            "recipient_nrp": copy.recipient.nrp if copy.recipient else None,
            "recipient_nama": copy.recipient.nama if copy.recipient else None,
        },
        "canary_beacon",
    )
    session.commit()

    accept = request.headers.get("accept", "")
    if "text/html" in accept and accept != "*/*":
        doc_nomor = copy.document.nomor if copy.document else "NASKAH-DINAS"
        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>Verifikasi Integritas Naskah Dinas</title>
  <style>
    body {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      background: #090d16;
      color: #10b981;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }}
    .card {{
      background: #111827;
      border: 1px solid #1f2937;
      border-radius: 8px;
      padding: 2rem;
      text-align: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      max-width: 420px;
    }}
    .badge {{
      display: inline-block;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: bold;
      letter-spacing: 0.05em;
      margin-bottom: 1rem;
    }}
    h1 {{ font-size: 1rem; margin: 0 0 0.5rem 0; color: #f9fafb; }}
    p {{ font-size: 0.8rem; color: #9ca3af; margin: 0 0 1rem 0; }}
    .id {{ font-size: 0.75rem; color: #6b7280; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">SIDIK · PUSSIBERAD</div>
    <h1>Naskah Dinas Terverifikasi</h1>
    <p>Integritas dokumen dan tanda tangan kriptografis valid.</p>
    <div class="id">DOKUMEN: {doc_nomor} · ID: {hex(copy.copy_id).upper()}</div>
  </div>
</body>
</html>"""
        return Response(
            content=html,
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    return Response(
        content=_TRANSPARENT_GIF_1X1,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
