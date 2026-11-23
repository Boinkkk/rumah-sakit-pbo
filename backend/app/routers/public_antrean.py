from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AntreanModel, PasienModel
from app.database.session import get_db_session
from app.domain.enums import JenisPoli, StatusAntrean, TingkatUrgensi
from app.domain.pasien import Pasien
from app.repositories.clinic_repositories import AntreanRepository
from app.repositories.pasien_repository import PasienRepository, model_to_pasien_domain
from app.routers.ws import ws_manager
from app.schemas.schemas import (
    PublicAntreanPasienBaruRequest,
    PublicAntreanPasienLamaRequest,
)
from app.services.antrean_manager import AntreanManager, PRIORITAS_WEIGHT

router = APIRouter(prefix="/api/public/antrean", tags=["Portal Pasien Mandiri"])


def _mask_nama(nama: str) -> str:
    """Menyamarkan nama pasien untuk tampilan papan monitor ruang tunggu publik."""
    parts = [p for p in (nama or "").strip().split() if p]
    if not parts:
        return "-"
    if len(parts) == 1:
        word = parts[0]
        return f"{word[0]}{'*' * max(2, len(word) - 1)}"
    return f"{parts[0]} {parts[1][0]}."


def _determine_public_prioritas(pasien: Pasien) -> str:
    """Portal pasien hanya mendukung Reguler atau otomatis Lansia (usia >= 60 tahun)."""
    if pasien.hitung_umur() >= 60:
        return TingkatUrgensi.LANSIA
    return TingkatUrgensi.REGULER


async def _build_personal_ticket_response(
    manager: AntreanManager,
    antrean: AntreanModel,
    sudah_terdaftar: bool = False,
) -> dict:
    ahead = await manager.count_ahead_in_poli_db(antrean)
    return {
        "id": antrean.id,
        "nomor_antrean": antrean.nomor_antrean,
        "pasien_nomor_rm": antrean.pasien_nomor_rm,
        "pasien_nama": antrean.pasien.nama if antrean.pasien else "",
        "poli_tujuan": antrean.poli_tujuan,
        "prioritas": antrean.prioritas,
        "status": antrean.status,
        "waktu_daftar": antrean.waktu_daftar.isoformat(),
        "antrean_di_depan": ahead,
        "sudah_terdaftar_hari_ini": sudah_terdaftar,
    }


async def _verify_pasien_lama(
    repo: PasienRepository,
    identitas: str,
    tanggal_lahir: date,
) -> PasienModel:
    cleaned = identitas.strip()
    pasien = await repo.get_by_nik(cleaned)
    if pasien is None:
        pasien = await repo.get_by_nomor_rm(cleaned.upper())
    if pasien is None or pasien.tanggal_lahir != tanggal_lahir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data pasien tidak cocok. Periksa kembali NIK/Nomor RM dan tanggal lahir Anda.",
        )
    if not pasien.aktif:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profil pasien berstatus nonaktif. Silakan hubungi loket pendaftaran klinik.",
        )
    return pasien


@router.get("/monitor")
async def get_public_monitor(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Endpoint publik papan monitor antrean ruang tunggu tanpa mengekspos data medis sensitif."""
    repo = AntreanRepository(session)
    items = await repo.list_today()

    poli_summaries = []
    for poli in (JenisPoli.POLI_UMUM, JenisPoli.POLI_GIGI, JenisPoli.POLI_ANAK):
        poli_items = [a for a in items if a.poli_tujuan == poli]
        diperiksa = next(
            (a for a in poli_items if a.status == StatusAntrean.DIPERIKSA), None
        )
        menunggu = [a for a in poli_items if a.status == StatusAntrean.MENUNGGU]
        menunggu.sort(
            key=lambda a: (
                PRIORITAS_WEIGHT.get(a.prioritas, 2),
                a.waktu_daftar,
                a.id,
            )
        )
        poli_summaries.append(
            {
                "poli_tujuan": poli,
                "sedang_dipanggil": (
                    {
                        "nomor_antrean": diperiksa.nomor_antrean,
                        "nama_samaran": _mask_nama(
                            diperiksa.pasien.nama if diperiksa.pasien else ""
                        ),
                    }
                    if diperiksa
                    else None
                ),
                "jumlah_menunggu": len(menunggu),
                "berikutnya": [
                    {
                        "nomor_antrean": m.nomor_antrean,
                        "nama_samaran": _mask_nama(m.pasien.nama if m.pasien else ""),
                        "prioritas": m.prioritas,
                    }
                    for m in menunggu[:5]
                ],
            }
        )

    return {
        "poli": poli_summaries,
        "total_menunggu": sum(1 for a in items if a.status == StatusAntrean.MENUNGGU),
    }


@router.post("/pasien-lama", status_code=status.HTTP_201_CREATED)
async def ambil_antrean_pasien_lama(
    payload: PublicAntreanPasienLamaRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Ambil nomor antrean mandiri untuk pasien terdaftar via NIK/NRM + Tanggal Lahir."""
    pasien_repo = PasienRepository(session)
    pasien_model = await _verify_pasien_lama(
        pasien_repo, payload.identitas, payload.tanggal_lahir
    )

    manager = AntreanManager(session)
    existing = await manager.find_active_antrean_today_db(pasien_model.nomor_rm)
    if existing is not None:
        return await _build_personal_ticket_response(
            manager, existing, sudah_terdaftar=True
        )

    domain_pasien = model_to_pasien_domain(pasien_model)
    prioritas = _determine_public_prioritas(domain_pasien)
    antrean = await manager.daftar_antrean_db(
        pasien_nomor_rm=pasien_model.nomor_rm,
        poli_tujuan=payload.poli_tujuan,
        prioritas=prioritas,
    )
    resp = await _build_personal_ticket_response(manager, antrean, sudah_terdaftar=False)
    await ws_manager.broadcast("antrean_updated", {"nomor_antrean": antrean.nomor_antrean})
    return resp


@router.post("/pasien-baru", status_code=status.HTTP_201_CREATED)
async def ambil_antrean_pasien_baru(
    payload: PublicAntreanPasienBaruRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Registrasi pasien baru mandiri sekaligus penerbitan tiket antrean poli."""
    pasien_repo = PasienRepository(session)
    existing_nik = await pasien_repo.get_by_nik(payload.nik)
    if existing_nik is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NIK sudah terdaftar di klinik. Silakan gunakan tab 'Pasien Lama' dengan NIK dan tanggal lahir Anda.",
        )

    try:
        nomor_rm = await pasien_repo.generate_nomor_rm()
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
        pasien_model = PasienModel(
            nomor_rm=domain_pasien.get_nomor_rm(),
            nik=domain_pasien.get_nik(),
            nama=domain_pasien.get_nama(),
            tanggal_lahir=domain_pasien.get_tanggal_lahir(),
            jenis_kelamin=domain_pasien.get_jenis_kelamin(),
            alamat=domain_pasien.get_alamat(),
            no_telepon=domain_pasien.get_no_telepon(),
            riwayat_alergi=domain_pasien.get_riwayat_alergi(),
            aktif=True,
        )
        session.add(pasien_model)
        await session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    manager = AntreanManager(session)
    prioritas = _determine_public_prioritas(domain_pasien)
    antrean = await manager.daftar_antrean_db(
        pasien_nomor_rm=pasien_model.nomor_rm,
        poli_tujuan=payload.poli_tujuan,
        prioritas=prioritas,
    )
    resp = await _build_personal_ticket_response(manager, antrean, sudah_terdaftar=False)
    await ws_manager.broadcast("antrean_updated", {"nomor_antrean": antrean.nomor_antrean})
    return resp


@router.get("/cek")
async def cek_status_antrean_pasien(
    identitas: str = Query(..., min_length=3),
    tanggal_lahir: date = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Mengecek status antrean aktif pasien hari ini berdasarkan NIK/NRM + Tanggal Lahir."""
    pasien_repo = PasienRepository(session)
    pasien_model = await _verify_pasien_lama(pasien_repo, identitas, tanggal_lahir)
    manager = AntreanManager(session)
    active = await manager.find_active_antrean_today_db(pasien_model.nomor_rm)
    if active is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anda belum memiliki antrean aktif (Menunggu/Diperiksa) hari ini.",
        )
    return await _build_personal_ticket_response(manager, active, sudah_terdaftar=True)
