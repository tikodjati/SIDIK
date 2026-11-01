from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import intake, layer2, ledger, registry
from app.config import settings

app = FastAPI(
    title="SIDIK API",
    version="0.1.0",
    description="Sistem Identifikasi Dokumen dan Investigasi Kebocoran",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(layer2.router)
app.include_router(registry.router)
app.include_router(intake.router)
app.include_router(ledger.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
