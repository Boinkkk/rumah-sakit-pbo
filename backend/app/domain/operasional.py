from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from app.domain.enums import (
    MetodePembayaran,
    StatusAntrean,
    StatusResep,
    TingkatUrgensi,
)
from app.domain.layanan import LayananKlinik, PenjualanObat, TindakanMedis
from app.domain.obat import Obat

if TYPE_CHECKING:
    from app.domain.pasien import Pasien


class Antrean:
    """Entitas Antrean kunjungan pasien pada poli tujuan."""

    def __init__(
        self,
        nomor_antrean: str,
        poli_tujuan: str,
        pasien_nomor_rm: str,
        pasien_nama: str = "",
        prioritas: str = TingkatUrgensi.REGULER,
        status: str = StatusAntrean.MENUNGGU,
        waktu_daftar: datetime | None = None,
    ):
        self.__nomor_antrean = nomor_antrean
        self.__poli_tujuan = poli_tujuan
        self.__pasien_nomor_rm = pasien_nomor_rm
        self.__pasien_nama = pasien_nama
        self.__prioritas = prioritas
        self.__status = status
        self.__waktu_daftar = waktu_daftar or datetime.now()

    def get_nomor_antrean(self) -> str:
        return self.__nomor_antrean

    def get_poli_tujuan(self) -> str:
        return self.__poli_tujuan

    def get_pasien_nomor_rm(self) -> str:
        return self.__pasien_nomor_rm

    def get_pasien_nama(self) -> str:
        return self.__pasien_nama

    def get_prioritas(self) -> str:
        return self.__prioritas

    def get_status(self) -> str:
        return self.__status

    def get_waktu_daftar(self) -> datetime:
        return self.__waktu_daftar

    def panggil(self) -> None:
        if self.__status != StatusAntrean.MENUNGGU:
            raise ValueError(
                f"Antrean {self.__nomor_antrean} tidak dalam status Menunggu (status saat ini: {self.__status})."
            )
        self.__status = StatusAntrean.DIPERIKSA

    def selesaikan(self) -> None:
        if self.__status not in (StatusAntrean.DIPERIKSA, StatusAntrean.MENUNGGU):
            raise ValueError(
                f"Antrean {self.__nomor_antrean} sudah selesai atau tidak dapat diselesaikan."
            )
        self.__status = StatusAntrean.SELESAI_DIPERIKSA

    def tandai_lunas(self) -> None:
        self.__status = StatusAntrean.SELESAI

    def to_dict(self) -> dict:
        return {
            "nomor_antrean": self.__nomor_antrean,
            "poli_tujuan": self.__poli_tujuan,
            "pasien_nomor_rm": self.__pasien_nomor_rm,
            "pasien_nama": self.__pasien_nama,
            "prioritas": self.__prioritas,
            "status": self.__status,
            "waktu_daftar": self.__waktu_daftar.isoformat(),
        }


class ItemResep:
    """Aggregation item yang menghubungkan RekamMedis dengan entitas Obat."""

    def __init__(
        self,
        obat: Obat,
        jumlah: int = 1,
        dosis: str = "3x1 sesudah makan",
        biaya_racik: float = 0.0,
    ):
        if jumlah <= 0:
            raise ValueError("Jumlah obat pada resep minimal 1.")
        if biaya_racik < 0:
            raise ValueError("Biaya racik tidak boleh negatif.")
        self.obat = obat
        self.jumlah = int(jumlah)
        self.dosis = dosis.strip() or "3x1 sesudah makan"
        self.biaya_racik = float(biaya_racik)

    def to_penjualan_obat(self) -> PenjualanObat:
        return PenjualanObat(
            kode=self.obat.get_kode_obat(),
            nama=self.obat.get_nama_obat(),
            harga_satuan=self.obat.get_harga_satuan(),
            jumlah_beli=self.jumlah,
            biaya_racik=self.biaya_racik,
        )

    def to_dict(self) -> dict:
        return {
            "kode_obat": self.obat.get_kode_obat(),
            "nama_obat": self.obat.get_nama_obat(),
            "satuan": self.obat.get_satuan(),
            "harga_satuan": self.obat.get_harga_satuan(),
            "jumlah": self.jumlah,
            "dosis": self.dosis,
            "biaya_racik": self.biaya_racik,
            "subtotal": (self.obat.get_harga_satuan() * self.jumlah) + self.biaya_racik,
        }


class RekamMedis:
    """Entitas RekamMedis (Composition dengan Pasien, Aggregation dengan Obat)."""

    def __init__(
        self,
        id_rekam_medis: str,
        pasien_nomor_rm: str,
        dokter_id: str,
        keluhan_utama: str,
        diagnosis: str,
        tekanan_darah: str = "120/80 mmHg",
        suhu_tubuh: float = 36.5,
        denyut_nadi: int = 80,
        catatan_dokter: str = "",
        tanggal_periksa: date | None = None,
        status_resep: str = StatusResep.MENUNGGU_VALIDASI,
    ):
        if not keluhan_utama or not keluhan_utama.strip():
            raise ValueError("Keluhan utama pasien wajib diisi.")
        if not diagnosis or not diagnosis.strip():
            raise ValueError("Diagnosis penyakit wajib diisi.")
        self.__id_rekam_medis = id_rekam_medis
        self.__pasien_nomor_rm = pasien_nomor_rm
        self.__dokter_id = dokter_id
        self.__tanggal_periksa = tanggal_periksa or date.today()
        self.__keluhan_utama = keluhan_utama.strip()
        self.__tekanan_darah = tekanan_darah.strip() or "120/80 mmHg"
        self.__suhu_tubuh = float(suhu_tubuh)
        self.__denyut_nadi = int(denyut_nadi)
        self.__diagnosis = diagnosis.strip()
        self.__catatan_dokter = catatan_dokter.strip()
        self.__status_resep = status_resep
        self.__daftar_tindakan: list[TindakanMedis] = []
        self.__daftar_resep: list[ItemResep] = []

    def get_id_rekam_medis(self) -> str:
        return self.__id_rekam_medis

    def get_pasien_nomor_rm(self) -> str:
        return self.__pasien_nomor_rm

    def get_dokter_id(self) -> str:
        return self.__dokter_id

    def get_tanggal_periksa(self) -> date:
        return self.__tanggal_periksa

    def get_keluhan_utama(self) -> str:
        return self.__keluhan_utama

    def get_tekanan_darah(self) -> str:
        return self.__tekanan_darah

    def get_suhu_tubuh(self) -> float:
        return self.__suhu_tubuh

    def get_denyut_nadi(self) -> int:
        return self.__denyut_nadi

    def get_diagnosis(self) -> str:
        return self.__diagnosis

    def get_catatan_dokter(self) -> str:
        return self.__catatan_dokter

    def get_status_resep(self) -> str:
        return self.__status_resep

    def set_status_resep(self, status_resep: str) -> None:
        self.__status_resep = status_resep

    def get_daftar_tindakan(self) -> list[TindakanMedis]:
        return list(self.__daftar_tindakan)

    def get_daftar_resep(self) -> list[ItemResep]:
        return list(self.__daftar_resep)

    def tambah_tindakan(self, t: TindakanMedis) -> None:
        self.__daftar_tindakan.append(t)

    def tambah_resep(
        self,
        o: Obat,
        jumlah: int = 1,
        dosis: str = "3x1 sesudah makan",
        biaya_racik: float = 0.0,
    ) -> None:
        self.__daftar_resep.append(
            ItemResep(obat=o, jumlah=jumlah, dosis=dosis, biaya_racik=biaya_racik)
        )

    def to_dict(self) -> dict:
        return {
            "id_rekam_medis": self.__id_rekam_medis,
            "pasien_nomor_rm": self.__pasien_nomor_rm,
            "dokter_id": self.__dokter_id,
            "tanggal_periksa": self.__tanggal_periksa.isoformat(),
            "keluhan_utama": self.__keluhan_utama,
            "tekanan_darah": self.__tekanan_darah,
            "suhu_tubuh": self.__suhu_tubuh,
            "denyut_nadi": self.__denyut_nadi,
            "diagnosis": self.__diagnosis,
            "catatan_dokter": self.__catatan_dokter,
            "status_resep": self.__status_resep,
            "tindakan": [t.to_dict() for t in self.__daftar_tindakan],
            "resep": [r.to_dict() for r in self.__daftar_resep],
        }


class TransaksiPembayaran:
    """Mengagregasikan seluruh item LayananKlinik dalam satu tagihan faktur (Composition)."""

    def __init__(
        self,
        id_transaksi: str,
        pasien_nomor_rm: str = "",
        rekam_medis_id: str = "",
        waktu: datetime | None = None,
        nominal_bayar: float = 0.0,
        metode_pembayaran: str = MetodePembayaran.TUNAI,
        status_lunas: bool = False,
    ):
        self.__id_transaksi = id_transaksi
        self.__pasien_nomor_rm = pasien_nomor_rm
        self.__rekam_medis_id = rekam_medis_id
        self.__waktu = waktu or datetime.now()
        self.__nominal_bayar = float(nominal_bayar)
        self.__metode_pembayaran = metode_pembayaran
        self.__status_lunas = status_lunas
        self.__daftar_layanan: list[LayananKlinik] = []

    def get_id_transaksi(self) -> str:
        return self.__id_transaksi

    def get_pasien_nomor_rm(self) -> str:
        return self.__pasien_nomor_rm

    def get_rekam_medis_id(self) -> str:
        return self.__rekam_medis_id

    def get_waktu(self) -> datetime:
        return self.__waktu

    def get_nominal_bayar(self) -> float:
        return self.__nominal_bayar

    def get_metode_pembayaran(self) -> str:
        return self.__metode_pembayaran

    def is_lunas(self) -> bool:
        return self.__status_lunas

    def get_daftar_layanan(self) -> list[LayananKlinik]:
        return list(self.__daftar_layanan)

    def tambah_layanan(self, layanan: LayananKlinik) -> None:
        if not isinstance(layanan, LayananKlinik):
            raise TypeError("Objek layanan harus merupakan turunan dari LayananKlinik.")
        self.__daftar_layanan.append(layanan)

    def hitung_grand_total(self) -> float:
        """Kalkulasi total tagihan secara polimorfik tanpa pengondisian if-else manual."""
        return float(sum(layanan.hitung_total_biaya() for layanan in self.__daftar_layanan))

    def hitung_kembalian(self) -> float:
        grand_total = self.hitung_grand_total()
        return max(0.0, self.__nominal_bayar - grand_total)

    def proses_pembayaran(
        self,
        nominal_bayar: float,
        metode_pembayaran: str = MetodePembayaran.TUNAI,
    ) -> float:
        grand_total = self.hitung_grand_total()
        if nominal_bayar < grand_total:
            raise ValueError(
                f"Nominal bayar (Rp{nominal_bayar:,.0f}) kurang dari grand total tagihan (Rp{grand_total:,.0f})."
            )
        self.__nominal_bayar = float(nominal_bayar)
        self.__metode_pembayaran = metode_pembayaran
        self.__status_lunas = True
        self.__waktu = datetime.now()
        return self.hitung_kembalian()

    def cetak_struk(self) -> dict:
        grand_total = self.hitung_grand_total()
        return {
            "id_transaksi": self.__id_transaksi,
            "pasien_nomor_rm": self.__pasien_nomor_rm,
            "rekam_medis_id": self.__rekam_medis_id,
            "waktu": self.__waktu.isoformat(),
            "metode_pembayaran": self.__metode_pembayaran,
            "status_lunas": self.__status_lunas,
            "rincian_layanan": [l.to_dict() for l in self.__daftar_layanan],
            "grand_total": grand_total,
            "nominal_bayar": self.__nominal_bayar,
            "kembalian": self.hitung_kembalian() if self.__status_lunas else 0.0,
        }
