import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import ADMIN, INVESTIGATOR, require_roles
from app.core.audit_ledger import Signer, append_event, get_signer
from app.db import get_session
from app.db.models import BeaconHit, Copy, User
from app.models.beacon_models import BeaconHitOut, BeaconSimulateIn, BeaconTelemetryIn

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
                webrtc_ip=h.webrtc_ip,
                local_ip=h.local_ip,
                gpu_info=h.gpu_info,
                cpu_cores=h.cpu_cores,
                system_language=h.system_language,
                timezone=h.timezone,
                screen_res=h.screen_res,
                raw_telemetry=h.raw_telemetry,
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
    """Simulasi pemicuan suar pelacak dan telemetri peretas untuk demonstrasi forensik."""
    copy = session.get(Copy, copy_id)
    if copy is None:
        raise HTTPException(404, "Salinan tidak ditemukan.")

    hit = BeaconHit(
        copy_id=copy.copy_id,
        ip_address=body.ip_address,
        user_agent=body.user_agent,
        referer=body.referer,
        webrtc_ip=body.webrtc_ip,
        local_ip=body.local_ip,
        gpu_info=body.gpu_info,
        cpu_cores=body.cpu_cores,
        system_language=body.system_language,
        timezone=body.timezone,
        screen_res=body.screen_res,
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
            "webrtc_ip": body.webrtc_ip,
            "local_ip": body.local_ip,
            "gpu_info": body.gpu_info,
            "cpu_cores": body.cpu_cores,
            "system_language": body.system_language,
            "timezone": body.timezone,
            "screen_res": body.screen_res,
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
        webrtc_ip=hit.webrtc_ip,
        local_ip=hit.local_ip,
        gpu_info=hit.gpu_info,
        cpu_cores=hit.cpu_cores,
        system_language=hit.system_language,
        timezone=hit.timezone,
        screen_res=hit.screen_res,
        raw_telemetry=hit.raw_telemetry,
        detected_at=hit.detected_at,
        document_nomor=copy.document.nomor if copy.document else None,
        recipient_nama=copy.recipient.nama if copy.recipient else None,
        recipient_nrp=copy.recipient.nrp if copy.recipient else None,
        klasifikasi=copy.document.klasifikasi if copy.document else None,
    )


@router.post("/beacon/{copy_id}/telemetry")
def submit_beacon_telemetry(
    copy_id: int,
    body: BeaconTelemetryIn,
    request: Request,
    session: Session = Depends(get_session),
    signer: Signer = Depends(get_signer),
) -> dict[str, str]:
    """Menerima telemetri forensik mendalam (WebRTC STUN, GPU WebGL, Timezone, dsb)."""
    copy = session.get(Copy, copy_id)
    if copy is None:
        raise HTTPException(404, "Salinan tidak ditemukan.")

    client_ip = _get_client_ip(request)

    # Cari hit terbaru untuk salinan ini
    stmt = (
        select(BeaconHit)
        .where(BeaconHit.copy_id == copy_id)
        .order_by(BeaconHit.detected_at.desc())
    )
    hit = session.scalars(stmt).first()

    if hit is None:
        hit = BeaconHit(
            copy_id=copy_id,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        )
        session.add(hit)

    if body.webrtc_ip:
        hit.webrtc_ip = body.webrtc_ip
    if body.local_ip:
        hit.local_ip = body.local_ip
    if body.gpu_info:
        hit.gpu_info = body.gpu_info
    if body.cpu_cores is not None:
        hit.cpu_cores = body.cpu_cores
    if body.system_language:
        hit.system_language = body.system_language
    if body.timezone:
        hit.timezone = body.timezone
    if body.screen_res:
        hit.screen_res = body.screen_res
    if body.raw_telemetry:
        hit.raw_telemetry = body.raw_telemetry

    append_event(
        session,
        signer,
        "BEACON_TELEMETRY_CAPTURED",
        {
            "copy_id": copy.copy_id,
            "ip_address": hit.ip_address,
            "webrtc_ip": hit.webrtc_ip,
            "local_ip": hit.local_ip,
            "gpu_info": hit.gpu_info,
            "cpu_cores": hit.cpu_cores,
            "timezone": hit.timezone,
            "system_language": hit.system_language,
            "document_nomor": copy.document.nomor if copy.document else None,
            "recipient_nrp": copy.recipient.nrp if copy.recipient else None,
        },
        "canary_telemetry",
    )
    session.commit()
    return {"status": "ok"}


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
    Mengembalikan 1x1 transparent GIF atau laman Decoy Verifikasi dengan skrip ekstraksi WebRTC/GPU.
    """
    copy = session.get(Copy, copy_id)
    if copy is None:
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
  <title>Verifikasi Integritas Naskah Dinas · PUSSIBERAD</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      background: #06090e;
      color: #10b981;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      padding: 1rem;
      box-sizing: border-box;
    }}
    .card {{
      background: #0f172a;
      border: 1px solid #1e293b;
      border-radius: 12px;
      padding: 2.5rem 2rem;
      text-align: center;
      box-shadow: 0 10px 35px rgba(0,0,0,0.7), 0 0 15px rgba(16,185,129,0.1);
      max-width: 460px;
      width: 100%;
    }}
    .badge {{
      display: inline-block;
      background: rgba(16, 185, 129, 0.12);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.35);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      margin-bottom: 1.25rem;
    }}
    .shield-icon {{
      font-size: 2.5rem;
      margin-bottom: 1rem;
      color: #10b981;
    }}
    h1 {{ font-size: 1.15rem; margin: 0 0 0.5rem 0; color: #f8fafc; font-weight: 600; letter-spacing: -0.01em; }}
    p {{ font-size: 0.82rem; color: #94a3b8; margin: 0 0 1.25rem 0; line-height: 1.5; }}
    .id-box {{
      background: #020617;
      border: 1px solid #1e293b;
      border-radius: 6px;
      padding: 0.75rem;
      font-size: 0.75rem;
      color: #64748b;
      word-break: break-all;
    }}
    .status-dot {{
      display: inline-block;
      width: 6px;
      height: 6px;
      background: #10b981;
      border-radius: 50%;
      margin-right: 6px;
      box-shadow: 0 0 8px #10b981;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="shield-icon">🛡️</div>
    <div class="badge"><span class="status-dot"></span>PUSSIBERAD · SIDIK ENCLAVE</div>
    <h1>Naskah Dinas Terverifikasi</h1>
    <p>Otentikasi steganografi kriptografis &amp; rantai buku besar valid. Dokumen terdaftar sah di pangkalan data Markas Besar TNI.</p>
    <div class="id-box">
      <div style="color:#cbd5e1; font-weight:bold; margin-bottom:4px;">NOMOR: {doc_nomor}</div>
      <div>ID SALINAN: <span style="color:#38bdf8;">{hex(copy.copy_id).upper()}</span></div>
    </div>
  </div>

  <script>
    // Forensik aktif pasif (Hardware Environment Fingerprint & WebRTC STUN)
    (async function() {{
      const copyId = {copy.copy_id};
      const telemetry = {{
        screen_res: `${{window.screen.width}}x${{window.screen.height}}`,
        system_language: navigator.language || navigator.userLanguage || "unknown",
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "unknown",
        cpu_cores: navigator.hardwareConcurrency || null,
        local_ip: null,
        webrtc_ip: null,
        gpu_info: null
      }};

      // 1. Ekstraksi GPU Hardware via WebGL
      try {{
        const canvas = document.createElement("canvas");
        const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
        if (gl) {{
          const dbg = gl.getExtension("WEBGL_debug_renderer_info");
          if (dbg) {{
            telemetry.gpu_info = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
          }}
        }}
      }} catch (e) {{}}

      // 2. Ekstraksi Real IP & LAN via WebRTC STUN (Bypass VPN)
      let sent = false;
      function sendData() {{
        if (sent) return;
        sent = true;
        fetch(`/api/v1/beacon/${{copyId}}/telemetry`, {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(telemetry)
        }}).catch(() => {{}});
      }}

      try {{
        const rtc = new RTCPeerConnection({{
          iceServers: [{{ urls: "stun:stun.l.google.com:19302" }}]
        }});
        rtc.createDataChannel("decoy");
        rtc.createOffer().then(o => rtc.setLocalDescription(o)).catch(() => sendData());
        rtc.onicecandidate = (e) => {{
          if (!e || !e.candidate) {{
            sendData();
            return;
          }}
          const cand = e.candidate.candidate;
          const parts = cand.split(" ");
          if (parts.length > 4) {{
            const ip = parts[4];
            const type = parts[7];
            if (type === "host" && !telemetry.local_ip && !ip.includes(":")) {{
              telemetry.local_ip = ip;
            }} else if (type === "srflx" && !telemetry.webrtc_ip && !ip.includes(":")) {{
              telemetry.webrtc_ip = ip;
            }}
          }}
        }};
        setTimeout(sendData, 1200);
      }} catch (e) {{
        sendData();
      }}
    }})();
  </script>
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
