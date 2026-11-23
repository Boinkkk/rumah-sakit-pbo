from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    DetailLayananTransaksiModel,
    PenggunaModel,
    RekamMedisModel,
    TransaksiPembayaranModel,
)
from app.domain.enums import MetodePembayaran, StatusAntrean
from app.domain.layanan import KonsultasiDokter, PenjualanObat, TindakanMedis
from app.domain.operasional import TransaksiPembayaran
from app.repositories.clinic_repositories import (
    AntreanRepository,
    PenggunaRepository,
    RekamMedisRepository,
    TransaksiRepository,
)


class BillingService:
    """Service Engine untuk kalkulasi tagihan polimorfik dan pemrosesan pembayaran kasir."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._trx_repo = TransaksiRepository(session)
        self._rm_repo = RekamMedisRepository(session)
        self._user_repo = PenggunaRepository(session)
        self._antrean_repo = AntreanRepository(session)

    def build_domain_transaksi(
        self,
        id_transaksi: str,
        rm_model: RekamMedisModel,
        dokter_model: PenggunaModel,
        existing_trx: TransaksiPembayaranModel | None = None,
    ) -> TransaksiPembayaran:
        """Membentuk objek TransaksiPembayaran dan seluruh item LayananKlinik secara polimorfik."""
        trx = TransaksiPembayaran(
            id_transaksi=id_transaksi,
            pasien_nomor_rm=rm_model.pasien_nomor_rm,
            rekam_medis_id=rm_model.id_rekam_medis,
            waktu=existing_trx.waktu if existing_trx else datetime.now(),
            nominal_bayar=existing_trx.nominal_bayar if existing_trx else 0.0,
            metode_pembayaran=(
                existing_trx.metode_pembayaran if existing_trx else MetodePembayaran.TUNAI
            ),
            status_lunas=existing_trx.status_lunas if existing_trx else False,
        )

        # 1. KonsultasiDokter
        poli_code = (dokter_model.poli_praktik or "UMUM").replace("Poli ", "").upper()
        trx.tambah_layanan(
            KonsultasiDokter(
                kode=f"KONS-{poli_code}",
                nama=f"Konsultasi {dokter_model.nama_lengkap} ({dokter_model.spesialisasi or 'Dokter'})",
                tarif_dasar=dokter_model.tarif_konsultasi or 50000.0,
                tunjangan_spesialis=dokter_model.tunjangan_spesialis or 0.0,
            )
        )

        # 2. TindakanMedis
        for t in rm_model.tindakan_list:
            trx.tambah_layanan(
                TindakanMedis(
                    kode=t.kode_layanan,
                    nama=t.nama_layanan,
                    tarif_dasar=t.tarif_dasar,
                    biaya_alat_habis_pakai=t.biaya_alat_habis_pakai,
                )
            )

        # 3. PenjualanObat
        for r in rm_model.resep_list:
            trx.tambah_layanan(
                PenjualanObat(
                    kode=r.kode_obat,
                    nama=r.nama_obat,
                    harga_satuan=r.harga_satuan,
                    jumlah_beli=r.jumlah_beli,
                    biaya_racik=r.biaya_racik,
                )
            )

        return trx

    async def create_or_sync_tagihan(self, rekam_medis_id: str) -> TransaksiPembayaranModel:
        rm_model = await self._rm_repo.get_by_id(rekam_medis_id)
        if rm_model is None:
            raise ValueError(f"Rekam medis '{rekam_medis_id}' tidak ditemukan.")

        dokter_model = await self._user_repo.get_by_id(rm_model.dokter_id)
        if dokter_model is None:
            raise ValueError(f"Data dokter '{rm_model.dokter_id}' tidak ditemukan.")

        existing = await self._trx_repo.get_by_rekam_medis_id(rekam_medis_id)
        id_trx = existing.id_transaksi if existing else await self._trx_repo.generate_id()

        domain_trx = self.build_domain_transaksi(id_trx, rm_model, dokter_model, existing)
        grand_total = domain_trx.hitung_grand_total()

        if existing is None:
            trx_model = TransaksiPembayaranModel(
                id_transaksi=id_trx,
                pasien_nomor_rm=rm_model.pasien_nomor_rm,
                rekam_medis_id=rm_model.id_rekam_medis,
                waktu=domain_trx.get_waktu(),
                grand_total=grand_total,
                nominal_bayar=0.0,
                kembalian=0.0,
                metode_pembayaran=MetodePembayaran.TUNAI,
                status_lunas=False,
            )
            self._session.add(trx_model)
        else:
            trx_model = existing
            trx_model.grand_total = grand_total
            trx_model.layanan_list.clear()

        for layanan in domain_trx.get_daftar_layanan():
            data = layanan.to_dict()
            tambahan = (
                data.get("tunjangan_spesialis")
                or data.get("biaya_alat_habis_pakai")
                or data.get("biaya_racik")
                or 0.0
            )
            trx_model.layanan_list.append(
                DetailLayananTransaksiModel(
                    tipe_layanan=data["tipe_layanan"],
                    kode_layanan=data["kode_layanan"],
                    nama_layanan=data["nama_layanan"],
                    tarif_dasar=data["tarif_dasar"],
                    biaya_tambahan=tambahan,
                    jumlah=data.get("jumlah_beli", 1),
                    subtotal=data["total_biaya"],
                )
            )

        await self._session.commit()
        loaded = await self._trx_repo.get_by_id(trx_model.id_transaksi)
        assert loaded is not None
        return loaded

    async def proses_pembayaran(
        self,
        id_transaksi: str,
        nominal_bayar: float,
        metode_pembayaran: str,
        kasir_id: str,
    ) -> dict:
        trx_model = await self._trx_repo.get_by_id(id_transaksi)
        if trx_model is None:
            raise ValueError(f"Transaksi '{id_transaksi}' tidak ditemukan.")
        if trx_model.status_lunas:
            raise ValueError(f"Transaksi '{id_transaksi}' sudah berstatus Lunas.")

        rm_model = await self._rm_repo.get_by_id(trx_model.rekam_medis_id)
        if rm_model is None:
            raise ValueError("Rekam medis terkait transaksi tidak ditemukan.")
        dokter_model = await self._user_repo.get_by_id(rm_model.dokter_id)
        if dokter_model is None:
            raise ValueError("Data dokter terkait transaksi tidak ditemukan.")

        domain_trx = self.build_domain_transaksi(
            trx_model.id_transaksi, rm_model, dokter_model, trx_model
        )
        kembalian = domain_trx.proses_pembayaran(nominal_bayar, metode_pembayaran)

        trx_model.nominal_bayar = domain_trx.get_nominal_bayar()
        trx_model.kembalian = kembalian
        trx_model.metode_pembayaran = domain_trx.get_metode_pembayaran()
        trx_model.status_lunas = True
        trx_model.kasir_id = kasir_id
        trx_model.waktu = domain_trx.get_waktu()
        trx_model.grand_total = domain_trx.hitung_grand_total()

        if rm_model.antrean_id:
            antrean = await self._antrean_repo.get_by_id(rm_model.antrean_id)
            if antrean is not None:
                antrean.status = StatusAntrean.SELESAI

        await self._session.commit()
        return domain_trx.cetak_struk()
