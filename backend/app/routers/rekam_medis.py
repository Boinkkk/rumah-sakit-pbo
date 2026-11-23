from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_claims, require_roles
from app.database.models import RekamMedisModel
from app.database.session import get_db_session
from app.domain.enums import PeranPengguna
from app.repositories.clinic_repositories import PenggunaRepository, RekamMedisRepository
from app.routers.ws import ws_manager
from app.schemas.schemas import RekamMedisCreate
from app.services.rekam_medis_service import RekamMedisService

router = APIRouter(prefix="/api/rekam-medis", tags=["Rekam Medis"])


def serialize_rekam_medis(rm: RekamMedisModel, dokter_nama: str = "") -> dict:
    return {
        "id_rekam_medis": rm.id_rekam_medis,
        "pasien_nomor_rm": rm.pasien_nomor_rm,
        "pasien_nama": rm.pasien.nama if rm.pasien else "",
        "riwayat_alergi": rm.pasien.riwayat_alergi if rm.pasien else "Tidak ada",
        "dokter_id": rm.dokter_id,
        "dokter_nama": dokter_nama,
        "antrean_id": rm.antrean_id,
        "tanggal_periksa": rm.tanggal_periksa.isoformat(),
        "keluhan_utama": rm.keluhan_utama,
        "tekanan_darah": rm.tekanan_darah,
        "suhu_tubuh": rm.suhu_tubuh,
        "denyut_nadi": rm.denyut_nadi,
        "diagnosis": rm.diagnosis,
        "catatan_dokter": rm.catatan_dokter,
        "status_resep": rm.status_resep,
        "tindakan": [
            {
                "id": t.id,
                "kode_layanan": t.kode_layanan,
                "nama_layanan": t.nama_layanan,
                "tarif_dasar": t.tarif_dasar,
                "biaya_alat_habis_pakai": t.biaya_alat_habis_pakai,
                "subtotal": t.tarif_dasar + t.biaya_alat_habis_pakai,
            }
            for t in rm.tindakan_list
        ],
        "resep": [
            {
                "id": r.id,
                "kode_obat": r.kode_obat,
                "nama_obat": r.nama_obat,
                "jumlah_beli": r.jumlah_beli,
                "dosis": r.dosis,
                "harga_satuan": r.harga_satuan,
                "biaya_racik": r.biaya_racik,
                "tervalidasi": r.tervalidasi,
                "subtotal": (r.harga_satuan * r.jumlah_beli) + r.biaya_racik,
            }
            for r in rm.resep_list
        ],
        "created_at": rm.created_at.isoformat(),
    }


@router.get("")
async def list_rekam_medis(
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    repo = RekamMedisRepository(session)
    user_repo = PenggunaRepository(session)
    dokter_map = {d.id_pengguna: d.nama_lengkap for d in await user_repo.list_dokter()}
    rows = await repo.list_all()
    return [serialize_rekam_medis(r, dokter_map.get(r.dokter_id, r.dokter_id)) for r in rows]


@router.get("/pasien/{nomor_rm}")
async def list_rekam_medis_pasien(
    nomor_rm: str,
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    repo = RekamMedisRepository(session)
    user_repo = PenggunaRepository(session)
    dokter_map = {d.id_pengguna: d.nama_lengkap for d in await user_repo.list_dokter()}
    rows = await repo.list_by_pasien(nomor_rm)
    return [serialize_rekam_medis(r, dokter_map.get(r.dokter_id, r.dokter_id)) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_rekam_medis(
    payload: RekamMedisCreate,
    claims: dict = Depends(require_roles(PeranPengguna.DOKTER)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    service = RekamMedisService(session)
    try:
        rm = await service.simpan_pemeriksaan(
            pasien_nomor_rm=payload.pasien_nomor_rm,
            dokter_id=claims["sub"],
            keluhan_utama=payload.keluhan_utama,
            diagnosis=payload.diagnosis,
            tekanan_darah=payload.tekanan_darah,
            suhu_tubuh=payload.suhu_tubuh,
            denyut_nadi=payload.denyut_nadi,
            catatan_dokter=payload.catatan_dokter,
            antrean_id=payload.antrean_id,
            tindakan_items=[t.model_dump() for t in payload.tindakan],
            resep_items=[r.model_dump() for r in payload.resep],
        )
        data = serialize_rekam_medis(rm, claims.get("nama_lengkap", ""))
        await ws_manager.broadcast("rekam_medis_created", {"id_rekam_medis": rm.id_rekam_medis})
        return data
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
