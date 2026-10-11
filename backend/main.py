from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import agent, anomalies, audit, evaluation, pos, simulate, skus
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

origins = settings.cors_origins_list
allow_origins = ["*"] if ("*" in origins or not origins) else origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True if "*" not in allow_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (pos, anomalies, agent, audit, simulate, skus, evaluation):
    app.include_router(r.router, prefix="/api/v1")



@app.get("/health")
def health():
    return {"status": "ok"}
