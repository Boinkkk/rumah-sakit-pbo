from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_claims
from app.database.models import (
    AntreanModel,
    ObatModel,
    PasienModel,
    RekamMedisModel,
    TransaksiPembayaranModel,
)
from app.database.session import get_db_session
from app.domain.enums import StatusAntrean, StatusResep

router = APIRouter(prefix="/api/laporan", tags=["Laporan Operasional"])


@router.get("/ringkasan")
async def get_ringkasan_operasional(
    tanggal_mulai: date | None = Query(default=None),
    tanggal_akhir: date | None = Query(default=None),
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    today = date.today()
    start_date = tanggal_mulai or (today - timedelta(days=6))
    end_date = tanggal_akhir or today

    today_start = datetime.combine(today, datetime.min.time())
    range_start = datetime.combine(start_date, datetime.min.time())
    range_end = datetime.combine(end_date, datetime.max.time())

    # Antrean hari ini
    antrean_res = await session.execute(
        select(AntreanModel).where(AntreanModel.waktu_daftar >= today_start)
    )
    antrean_hari_ini = list(antrean_res.scalars().all())

    sedang_diperiksa = next(
        (a for a in antrean_hari_ini if a.status == StatusAntrean.DIPERIKSA), None
    )

    # Transaksi dalam rentang
    trx_res = await session.execute(
        select(TransaksiPembayaranModel).where(
            TransaksiPembayaranModel.waktu >= range_start,
            TransaksiPembayaranModel.waktu <= range_end,
        )
    )
    transaksi_range = list(trx_res.scalars().all())
    transaksi_lunas = [t for t in transaksi_range if t.status_lunas]
    total_pendapatan_hari_ini = sum(
        t.grand_total for t in transaksi_lunas if t.waktu >= today_start
    )
    total_pendapatan_periode = sum(t.grand_total for t in transaksi_lunas)

    # Resep menunggu validasi
    resep_res = await session.execute(
        select(RekamMedisModel).where(
            RekamMedisModel.status_resep == StatusResep.MENUNGGU_VALIDASI
        )
    )
    resep_menunggu = len(list(resep_res.scalars().all()))

    # Tagihan belum lunas
    tagihan_res = await session.execute(
        select(TransaksiPembayaranModel).where(
            TransaksiPembayaranModel.status_lunas.is_(False)
        )
    )
    tagihan_belum_lunas = len(list(tagihan_res.scalars().all()))

    # Total pasien aktif & obat stok menipis
    pasien_res = await session.execute(
        select(PasienModel).where(PasienModel.aktif.is_(True))
    )
    total_pasien_aktif = len(list(pasien_res.scalars().all()))

    obat_res = await session.execute(select(ObatModel))
    obat_list = list(obat_res.scalars().all())
    stok_menipis = [
        {"kode_obat": o.kode_obat, "nama_obat": o.nama_obat, "stok": o.stok}
        for o in obat_list
        if o.stok <= 20
    ]

    # Distribusi poli hari ini
    poli_counts: dict[str, int] = {"Poli Umum": 0, "Poli Gigi": 0, "Poli Anak": 0}
    for a in antrean_hari_ini:
        poli_counts[a.poli_tujuan] = poli_counts.get(a.poli_tujuan, 0) + 1

    # Kunjungan dalam periode
    antrean_range_res = await session.execute(
        select(AntreanModel).where(
            AntreanModel.waktu_daftar >= range_start,
            AntreanModel.waktu_daftar <= range_end,
        )
    )
    antrean_range = list(antrean_range_res.scalars().all())

    harian_map: dict[str, dict] = {}
    cur = start_date
    while cur <= end_date:
        key = cur.isoformat()
        harian_map[key] = {"tanggal": key, "kunjungan": 0, "pendapatan": 0.0}
        cur += timedelta(days=1)

    for a in antrean_range:
        key = a.waktu_daftar.date().isoformat()
        if key in harian_map:
            harian_map[key]["kunjungan"] += 1

    for t in transaksi_lunas:
        key = t.waktu.date().isoformat()
        if key in harian_map:
            harian_map[key]["pendapatan"] += t.grand_total

    return {
        "tanggal_hari_ini": today.isoformat(),
        "pasien_hari_ini": len(antrean_hari_ini),
        "antrean_menunggu": sum(
            1 for a in antrean_hari_ini if a.status == StatusAntrean.MENUNGGU
        ),
        "sedang_diperiksa": (
            sedang_diperiksa.nomor_antrean if sedang_diperiksa else "-"
        ),
        "total_pendapatan_hari_ini": total_pendapatan_hari_ini,
        "total_pendapatan_periode": total_pendapatan_periode,
        "total_transaksi_lunas": len(transaksi_lunas),
        "resep_menunggu": resep_menunggu,
        "tagihan_belum_lunas": tagihan_belum_lunas,
        "total_pasien_aktif": total_pasien_aktif,
        "stok_menipis": stok_menipis,
        "distribusi_poli": poli_counts,
        "grafik_harian": list(harian_map.values()),
    }
