from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_claims, require_roles
from app.database.models import ObatModel
from app.database.session import get_db_session
from app.domain.enums import PeranPengguna, StatusResep
from app.domain.obat import Obat
from app.repositories.clinic_repositories import (
    ObatRepository,
    PenggunaRepository,
    RekamMedisRepository,
    model_to_obat_domain,
    model_to_pengguna_domain,
)
from app.routers.rekam_medis import serialize_rekam_medis
from app.routers.ws import ws_manager
from app.schemas.schemas import ObatCreate, ObatUpdate

router = APIRouter(tags=["Farmasi & Inventaris Obat"])


@router.get("/api/obat")
async def list_obat(
    q: str = Query(default=""),
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    repo = ObatRepository(session)
    rows = await repo.list_all(query=q)
    return [model_to_obat_domain(o).to_dict() for o in rows]


@router.post("/api/obat", status_code=status.HTTP_201_CREATED)
async def create_obat(
    payload: ObatCreate,
    _: dict = Depends(require_roles(PeranPengguna.PETUGAS_FARMASI)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = ObatRepository(session)
    try:
        kode = payload.kode_obat.strip().upper() if payload.kode_obat else await repo.generate_kode_obat()
        if await repo.get_by_kode(kode) is not None:
            raise ValueError(f"Kode obat '{kode}' sudah terdaftar.")
        domain = Obat(
            kode_obat=kode,
            nama_obat=payload.nama_obat,
            stok=payload.stok,
            harga_satuan=payload.harga_satuan,
            satuan=payload.satuan,
            kategori=payload.kategori,
        )
        model = ObatModel(
            kode_obat=domain.get_kode_obat(),
            nama_obat=domain.get_nama_obat(),
            stok=domain.get_stok(),
            harga_satuan=domain.get_harga_satuan(),
            satuan=domain.get_satuan(),
            kategori=domain.get_kategori(),
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        await ws_manager.broadcast("obat_updated", domain.to_dict())
        return domain.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api/obat/{kode_obat}")
async def update_obat(
    kode_obat: str,
    payload: ObatUpdate,
    _: dict = Depends(require_roles(PeranPengguna.PETUGAS_FARMASI)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = ObatRepository(session)
    model = await repo.get_by_kode(kode_obat)
    if model is None:
        raise HTTPException(status_code=404, detail="Data obat tidak ditemukan.")
    try:
        domain = model_to_obat_domain(model)
        if payload.nama_obat is not None:
            domain.set_nama_obat(payload.nama_obat)
        if payload.stok is not None:
            domain.set_stok(payload.stok)
        if payload.harga_satuan is not None:
            domain.set_harga_satuan(payload.harga_satuan)
        if payload.satuan is not None:
            domain.set_satuan(payload.satuan)
        if payload.kategori is not None:
            domain.set_kategori(payload.kategori)

        model.nama_obat = domain.get_nama_obat()
        model.stok = domain.get_stok()
        model.harga_satuan = domain.get_harga_satuan()
        model.satuan = domain.get_satuan()
        model.kategori = domain.get_kategori()
        await session.commit()
        await ws_manager.broadcast("obat_updated", domain.to_dict())
        return domain.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/farmasi/resep")
async def list_resep_farmasi(
    status_resep: str | None = Query(default=None),
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    rm_repo = RekamMedisRepository(session)
    user_repo = PenggunaRepository(session)
    dokter_map = {d.id_pengguna: d.nama_lengkap for d in await user_repo.list_dokter()}
    rows = await rm_repo.list_all(status_resep=status_resep)
    return [
        serialize_rekam_medis(r, dokter_map.get(r.dokter_id, r.dokter_id))
        for r in rows
        if len(r.resep_list) > 0
    ]


@router.post("/api/farmasi/resep/{id_rekam_medis}/validasi")
async def validasi_resep(
    id_rekam_medis: str,
    claims: dict = Depends(require_roles(PeranPengguna.PETUGAS_FARMASI)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    rm_repo = RekamMedisRepository(session)
    obat_repo = ObatRepository(session)
    user_repo = PenggunaRepository(session)

    rm_model = await rm_repo.get_by_id(id_rekam_medis)
    if rm_model is None:
        raise HTTPException(status_code=404, detail="Rekam medis / resep tidak ditemukan.")
    if rm_model.status_resep == StatusResep.DIVALIDASI:
        raise HTTPException(status_code=400, detail="Resep ini sudah divalidasi sebelumnya.")

    farmasi_model = await user_repo.get_by_id(claims["sub"])
    if farmasi_model is None:
        raise HTTPException(status_code=404, detail="Akun petugas farmasi tidak ditemukan.")
    farmasi_domain = model_to_pengguna_domain(farmasi_model)

    try:
        # Validasi stok & kurangi menggunakan domain Obat
        for item in rm_model.resep_list:
            obat_model = await obat_repo.get_by_kode(item.kode_obat)
            if obat_model is None:
                raise ValueError(f"Obat '{item.kode_obat}' tidak ditemukan di inventaris.")
            obat_domain = model_to_obat_domain(obat_model)
            obat_domain.kurangi_stok(item.jumlah_beli)
            obat_model.stok = obat_domain.get_stok()
            item.tervalidasi = True

        rm_model.status_resep = StatusResep.DIVALIDASI
        await session.commit()
        await session.refresh(rm_model)

        dokter_model = await user_repo.get_by_id(rm_model.dokter_id)
        dokter_nama = dokter_model.nama_lengkap if dokter_model else rm_model.dokter_id
        data = serialize_rekam_medis(rm_model, dokter_nama)
        data["divalidasi_oleh"] = farmasi_domain.nama_lengkap
        await ws_manager.broadcast("resep_validated", {"id_rekam_medis": id_rekam_medis})
        return data
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
