from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import agent, anomalies, audit, pos, simulate
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (pos, anomalies, agent, audit, simulate):
    app.include_router(r.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
