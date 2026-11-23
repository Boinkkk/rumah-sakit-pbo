from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_claims, require_roles
from app.database.models import AntreanModel
from app.database.session import get_db_session
from app.domain.enums import PeranPengguna
from app.repositories.clinic_repositories import AntreanRepository
from app.routers.ws import ws_manager
from app.schemas.schemas import AntreanCreate
from app.services.antrean_manager import AntreanManager, PRIORITAS_WEIGHT

router = APIRouter(prefix="/api/antrean", tags=["Antrean Poli"])


def serialize_antrean(a: AntreanModel) -> dict:
    return {
        "id": a.id,
        "nomor_antrean": a.nomor_antrean,
        "pasien_nomor_rm": a.pasien_nomor_rm,
        "pasien_nama": a.pasien.nama if a.pasien else "",
        "pasien_nik": a.pasien.nik if a.pasien else "",
        "riwayat_alergi": a.pasien.riwayat_alergi if a.pasien else "Tidak ada",
        "poli_tujuan": a.poli_tujuan,
        "prioritas": a.prioritas,
        "status": a.status,
        "waktu_daftar": a.waktu_daftar.isoformat(),
        "waktu_panggil": a.waktu_panggil.isoformat() if a.waktu_panggil else None,
    }


@router.get("")
async def list_antrean(
    poli: str | None = Query(default=None),
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    repo = AntreanRepository(session)
    items = await repo.list_today(poli=poli)
    items.sort(
        key=lambda a: (
            0 if a.status == "Diperiksa" else (1 if a.status == "Menunggu" else 2),
            PRIORITAS_WEIGHT.get(a.prioritas, 2) if a.status == "Menunggu" else 0,
            a.waktu_daftar,
            a.id,
        )
    )
    return [serialize_antrean(a) for a in items]


@router.post("", status_code=status.HTTP_201_CREATED)
async def daftar_antrean(
    payload: AntreanCreate,
    _: dict = Depends(require_roles(PeranPengguna.PETUGAS_ADMINISTRASI)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    manager = AntreanManager(session)
    try:
        antrean = await manager.daftar_antrean_db(
            pasien_nomor_rm=payload.pasien_nomor_rm,
            poli_tujuan=payload.poli_tujuan,
            prioritas=payload.prioritas,
        )
        data = serialize_antrean(antrean)
        await ws_manager.broadcast("antrean_updated", data)
        return data
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/panggil")
async def panggil_antrean_berikutnya(
    poli: str | None = Query(default=None),
    _: dict = Depends(require_roles(PeranPengguna.DOKTER)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    manager = AntreanManager(session)
    try:
        antrean = await manager.panggil_berikutnya_db(poli_tujuan=poli)
        data = serialize_antrean(antrean)
        await ws_manager.broadcast("antrean_called", data)
        return data
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
