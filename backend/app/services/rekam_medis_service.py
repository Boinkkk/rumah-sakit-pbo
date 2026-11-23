from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    DetailResepModel,
    DetailTindakanModel,
    RekamMedisModel,
)
from app.domain.enums import StatusAntrean, StatusResep
from app.domain.layanan import TindakanMedis
from app.domain.operasional import RekamMedis
from app.repositories.clinic_repositories import (
    AntreanRepository,
    ObatRepository,
    RekamMedisRepository,
    model_to_obat_domain,
)
from app.repositories.pasien_repository import PasienRepository
from app.services.billing_service import BillingService


class RekamMedisService:
    """Service Engine untuk pencatatan rekam medis, tindakan klinis, dan resep digital."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._rm_repo = RekamMedisRepository(session)
        self._pasien_repo = PasienRepository(session)
        self._obat_repo = ObatRepository(session)
        self._antrean_repo = AntreanRepository(session)

    async def simpan_pemeriksaan(
        self,
        pasien_nomor_rm: str,
        dokter_id: str,
        keluhan_utama: str,
        diagnosis: str,
        tekanan_darah: str,
        suhu_tubuh: float,
        denyut_nadi: int,
        catatan_dokter: str = "",
        antrean_id: int | None = None,
        tindakan_items: list[dict] | None = None,
        resep_items: list[dict] | None = None,
    ) -> RekamMedisModel:
        pasien = await self._pasien_repo.get_by_nomor_rm(pasien_nomor_rm)
        if pasien is None:
            raise ValueError(f"Pasien dengan NRM '{pasien_nomor_rm}' tidak ditemukan.")

        id_rm = await self._rm_repo.generate_id()
        has_resep = bool(resep_items)
        domain_rm = RekamMedis(
            id_rekam_medis=id_rm,
            pasien_nomor_rm=pasien.nomor_rm,
            dokter_id=dokter_id,
            keluhan_utama=keluhan_utama,
            diagnosis=diagnosis,
            tekanan_darah=tekanan_darah,
            suhu_tubuh=suhu_tubuh,
            denyut_nadi=denyut_nadi,
            catatan_dokter=catatan_dokter,
            tanggal_periksa=date.today(),
            status_resep=(
                StatusResep.MENUNGGU_VALIDASI if has_resep else StatusResep.DIVALIDASI
            ),
        )

        for t in tindakan_items or []:
            domain_rm.tambah_tindakan(
                TindakanMedis(
                    kode=t["kode_layanan"],
                    nama=t["nama_layanan"],
                    tarif_dasar=float(t["tarif_dasar"]),
                    biaya_alat_habis_pakai=float(t.get("biaya_alat_habis_pakai", 0.0)),
                )
            )

        for r in resep_items or []:
            obat_model = await self._obat_repo.get_by_kode(r["kode_obat"])
            if obat_model is None:
                raise ValueError(f"Obat dengan kode '{r['kode_obat']}' tidak ditemukan.")
            obat_domain = model_to_obat_domain(obat_model)
            if obat_domain.get_stok() < int(r["jumlah_beli"]):
                raise ValueError(
                    f"Stok obat '{obat_domain.get_nama_obat()}' tidak mencukupi (tersedia {obat_domain.get_stok()})."
                )
            domain_rm.tambah_resep(
                obat_domain,
                jumlah=int(r["jumlah_beli"]),
                dosis=r.get("dosis", "3x1 sesudah makan"),
                biaya_racik=float(r.get("biaya_racik", 0.0)),
            )

        rm_model = RekamMedisModel(
            id_rekam_medis=domain_rm.get_id_rekam_medis(),
            pasien_nomor_rm=domain_rm.get_pasien_nomor_rm(),
            dokter_id=domain_rm.get_dokter_id(),
            antrean_id=antrean_id,
            tanggal_periksa=domain_rm.get_tanggal_periksa(),
            keluhan_utama=domain_rm.get_keluhan_utama(),
            tekanan_darah=domain_rm.get_tekanan_darah(),
            suhu_tubuh=domain_rm.get_suhu_tubuh(),
            denyut_nadi=domain_rm.get_denyut_nadi(),
            diagnosis=domain_rm.get_diagnosis(),
            catatan_dokter=domain_rm.get_catatan_dokter(),
            status_resep=domain_rm.get_status_resep(),
            created_at=datetime.now(),
        )

        for t_dom in domain_rm.get_daftar_tindakan():
            rm_model.tindakan_list.append(
                DetailTindakanModel(
                    kode_layanan=t_dom.kode_layanan,
                    nama_layanan=t_dom.nama_layanan,
                    tarif_dasar=t_dom.tarif_dasar,
                    biaya_alat_habis_pakai=t_dom.biaya_alat_habis_pakai,
                )
            )

        for r_dom in domain_rm.get_daftar_resep():
            rm_model.resep_list.append(
                DetailResepModel(
                    kode_obat=r_dom.obat.get_kode_obat(),
                    nama_obat=r_dom.obat.get_nama_obat(),
                    jumlah_beli=r_dom.jumlah,
                    dosis=r_dom.dosis,
                    harga_satuan=r_dom.obat.get_harga_satuan(),
                    biaya_racik=r_dom.biaya_racik,
                    tervalidasi=False,
                )
            )

        self._session.add(rm_model)

        if antrean_id is not None:
            antrean_model = await self._antrean_repo.get_by_id(antrean_id)
            if antrean_model is not None:
                antrean_model.status = StatusAntrean.SELESAI_DIPERIKSA

        await self._session.commit()

        # Otomatis buat tagihan di modul kasir
        billing = BillingService(self._session)
        await billing.create_or_sync_tagihan(rm_model.id_rekam_medis)

        loaded = await self._rm_repo.get_by_id(rm_model.id_rekam_medis)
        assert loaded is not None
        return loaded
