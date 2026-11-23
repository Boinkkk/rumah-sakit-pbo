from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import APP_NAME, CLINIC_NAME
from app.database.seed import seed_database
from app.database.session import AsyncSessionLocal, init_db
from app.routers import (
    antrean,
    auth,
    farmasi,
    kasir,
    laporan,
    pasien,
    public_antrean,
    rekam_medis,
    ws,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_database(session)
    yield


app = FastAPI(
    title=f"{APP_NAME} API - {CLINIC_NAME}",
    description=(
        "Sistem Informasi Manajemen Layanan Klinik Kesehatan Berbasis Pemrograman "
        "Berorientasi Objek (React + FastAPI + SQLite)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Penanganan eksepsi global agar sistem tidak mengalami penghentian mendadak (crash)."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Terjadi kesalahan internal server: {exc}"},
    )


app.include_router(auth.router)
app.include_router(public_antrean.router)
app.include_router(pasien.router)
app.include_router(antrean.router)
app.include_router(rekam_medis.router)
app.include_router(farmasi.router)
app.include_router(kasir.router)
app.include_router(laporan.router)
app.include_router(ws.router)


@app.get("/api/health", tags=["Sistem"])
async def health_check() -> dict:
    return {
        "status": "ok",
        "app": APP_NAME,
        "clinic": CLINIC_NAME,
        "version": "1.0.0",
    }
