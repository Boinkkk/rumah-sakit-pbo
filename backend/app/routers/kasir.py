from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_claims, require_roles
from app.database.models import TransaksiPembayaranModel
from app.database.session import get_db_session
from app.domain.enums import PeranPengguna
from app.repositories.clinic_repositories import (
    RekamMedisRepository,
    TransaksiRepository,
)
from app.repositories.pasien_repository import PasienRepository
from app.routers.ws import ws_manager
from app.schemas.schemas import PembayaranRequest
from app.services.billing_service import BillingService

router = APIRouter(prefix="/api/kasir", tags=["Kasir & Pembayaran"])


async def serialize_transaksi(
    session: AsyncSession,
    trx: TransaksiPembayaranModel,
) -> dict:
    pasien_repo = PasienRepository(session)
    rm_repo = RekamMedisRepository(session)
    pasien = await pasien_repo.get_by_nomor_rm(trx.pasien_nomor_rm)
    rm = await rm_repo.get_by_id(trx.rekam_medis_id)

    return {
        "id_transaksi": trx.id_transaksi,
        "pasien_nomor_rm": trx.pasien_nomor_rm,
        "pasien_nama": pasien.nama if pasien else "",
        "pasien_nik": pasien.nik if pasien else "",
        "rekam_medis_id": trx.rekam_medis_id,
        "diagnosis": rm.diagnosis if rm else "",
        "status_resep": rm.status_resep if rm else "Divalidasi",
        "kasir_id": trx.kasir_id,
        "waktu": trx.waktu.isoformat(),
        "grand_total": trx.grand_total,
        "nominal_bayar": trx.nominal_bayar,
        "kembalian": trx.kembalian,
        "metode_pembayaran": trx.metode_pembayaran,
        "status_lunas": trx.status_lunas,
        "rincian_layanan": [
            {
                "id": item.id,
                "tipe_layanan": item.tipe_layanan,
                "kode_layanan": item.kode_layanan,
                "nama_layanan": item.nama_layanan,
                "tarif_dasar": item.tarif_dasar,
                "biaya_tambahan": item.biaya_tambahan,
                "jumlah": item.jumlah,
                "total_biaya": item.subtotal,
            }
            for item in trx.layanan_list
        ],
    }


@router.get("/tagihan")
async def list_tagihan(
    status_lunas: bool | None = Query(default=None),
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    repo = TransaksiRepository(session)
    rows = await repo.list_all(status_lunas=status_lunas)
    return [await serialize_transaksi(session, t) for t in rows]


@router.get("/tagihan/{id_transaksi}")
async def get_tagihan_detail(
    id_transaksi: str,
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = TransaksiRepository(session)
    trx = await repo.get_by_id(id_transaksi)
    if trx is None:
        raise HTTPException(status_code=404, detail="Data tagihan tidak ditemukan.")
    return await serialize_transaksi(session, trx)


@router.post("/tagihan/{id_transaksi}/bayar")
async def bayar_tagihan(
    id_transaksi: str,
    payload: PembayaranRequest,
    claims: dict = Depends(require_roles(PeranPengguna.KASIR)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    service = BillingService(session)
    try:
        struk = await service.proses_pembayaran(
            id_transaksi=id_transaksi,
            nominal_bayar=payload.nominal_bayar,
            metode_pembayaran=payload.metode_pembayaran,
            kasir_id=claims["sub"],
        )
        pasien_repo = PasienRepository(session)
        pasien = await pasien_repo.get_by_nomor_rm(struk["pasien_nomor_rm"])
        struk["pasien_nama"] = pasien.nama if pasien else ""
        struk["kasir_nama"] = claims.get("nama_lengkap", "")
        await ws_manager.broadcast("payment_completed", {"id_transaksi": id_transaksi})
        return struk
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
