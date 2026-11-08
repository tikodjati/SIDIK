from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, intake, layer2, ledger, registry, users
from app.config import settings
from app.core.audit_ledger import LedgerKeyMismatch

app = FastAPI(
    title="SIDIK API",
    version="0.1.0",
    description="Sistem Identifikasi Dokumen dan Investigasi Kebocoran",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(layer2.router)
app.include_router(registry.router)
app.include_router(intake.router)
app.include_router(ledger.router)


@app.exception_handler(LedgerKeyMismatch)
def _ledger_key_mismatch(_: Request, exc: LedgerKeyMismatch) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": f"Penulisan ditolak: {exc}"})


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
