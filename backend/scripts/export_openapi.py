"""Ekspor kontrak OpenAPI ke docs/openapi.json (sumber kebenaran untuk klien TS frontend)."""

import json
from pathlib import Path

from app.main import app

out = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"ditulis: {out}")
