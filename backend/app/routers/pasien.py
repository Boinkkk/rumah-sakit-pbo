from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_claims, require_roles
from app.database.models import PasienModel
from app.database.session import get_db_session
from app.domain.enums import PeranPengguna
from app.domain.pasien import Pasien
from app.repositories.pasien_repository import PasienRepository, model_to_pasien_domain
from app.schemas.schemas import PasienCreate, PasienUpdate

router = APIRouter(prefix="/api/pasien", tags=["Pasien"])


@router.get("")
async def list_pasien(
    q: str = Query(default="", description="Cari berdasarkan NRM, NIK, atau nama"),
    tanggal_lahir: date | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    repo = PasienRepository(session)
    rows = await repo.search_db(
        query=q, tanggal_lahir=tanggal_lahir, include_inactive=include_inactive
    )
    return [model_to_pasien_domain(r).to_dict() for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_pasien(
    payload: PasienCreate,
    _: dict = Depends(require_roles(PeranPengguna.PETUGAS_ADMINISTRASI)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = PasienRepository(session)
    try:
        existing_nik = await repo.get_by_nik(payload.nik)
        if existing_nik is not None:
            raise ValueError(
                f"NIK '{payload.nik}' sudah terdaftar atas nama {existing_nik.nama} ({existing_nik.nomor_rm})."
            )
        nomor_rm = await repo.generate_nomor_rm()
        domain_pasien = Pasien(
            nomor_rm=nomor_rm,
            nik=payload.nik,
            nama=payload.nama,
            tanggal_lahir=payload.tanggal_lahir,
            jenis_kelamin=payload.jenis_kelamin,
            alamat=payload.alamat,
            no_telepon=payload.no_telepon,
            riwayat_alergi=payload.riwayat_alergi,
            aktif=True,
        )
        model = PasienModel(
            nomor_rm=domain_pasien.get_nomor_rm(),
            nik=domain_pasien.get_nik(),
            nama=domain_pasien.get_nama(),
            tanggal_lahir=domain_pasien.get_tanggal_lahir(),
            jenis_kelamin=domain_pasien.get_jenis_kelamin(),
            alamat=domain_pasien.get_alamat(),
            no_telepon=domain_pasien.get_no_telepon(),
            riwayat_alergi=domain_pasien.get_riwayat_alergi(),
            aktif=domain_pasien.is_aktif(),
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return model_to_pasien_domain(model).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{nomor_rm}")
async def get_pasien(
    nomor_rm: str,
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = PasienRepository(session)
    model = await repo.get_by_nomor_rm(nomor_rm)
    if model is None:
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")
    return model_to_pasien_domain(model).to_dict()


@router.put("/{nomor_rm}")
async def update_pasien(
    nomor_rm: str,
    payload: PasienUpdate,
    _: dict = Depends(require_roles(PeranPengguna.PETUGAS_ADMINISTRASI)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = PasienRepository(session)
    model = await repo.get_by_nomor_rm(nomor_rm)
    if model is None:
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")

    try:
        domain = model_to_pasien_domain(model)
        if payload.nik is not None and payload.nik != domain.get_nik():
            dup = await repo.get_by_nik(payload.nik)
            if dup is not None and dup.nomor_rm != nomor_rm:
                raise ValueError(f"NIK '{payload.nik}' sudah digunakan pasien lain.")
            domain.set_nik(payload.nik)
        if payload.nama is not None:
            domain.set_nama(payload.nama)
        if payload.tanggal_lahir is not None:
            domain.set_tanggal_lahir(payload.tanggal_lahir)
        if payload.jenis_kelamin is not None:
            domain.set_jenis_kelamin(payload.jenis_kelamin)
        if payload.alamat is not None:
            domain.set_alamat(payload.alamat)
        if payload.no_telepon is not None:
            domain.set_no_telepon(payload.no_telepon)
        if payload.riwayat_alergi is not None:
            domain.set_riwayat_alergi(payload.riwayat_alergi)
        if payload.aktif is not None:
            if payload.aktif:
                domain.aktifkan()
            else:
                domain.nonaktifkan()

        model.nik = domain.get_nik()
        model.nama = domain.get_nama()
        model.tanggal_lahir = domain.get_tanggal_lahir()
        model.jenis_kelamin = domain.get_jenis_kelamin()
        model.alamat = domain.get_alamat()
        model.no_telepon = domain.get_no_telepon()
        model.riwayat_alergi = domain.get_riwayat_alergi()
        model.aktif = domain.is_aktif()

        await session.commit()
        await session.refresh(model)
        return domain.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{nomor_rm}/nonaktifkan")
async def deactivate_pasien(
    nomor_rm: str,
    _: dict = Depends(require_roles(PeranPengguna.PETUGAS_ADMINISTRASI)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = PasienRepository(session)
    model = await repo.get_by_nomor_rm(nomor_rm)
    if model is None:
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")
    domain = model_to_pasien_domain(model)
    domain.nonaktifkan()
    model.aktif = domain.is_aktif()
    await session.commit()
    return domain.to_dict()
