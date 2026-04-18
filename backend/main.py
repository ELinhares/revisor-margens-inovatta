from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import process

app = FastAPI(title="Revisor de Margens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(process.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
