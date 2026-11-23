from __future__ import annotations

from abc import ABC, abstractmethod


class LayananKlinik(ABC):
    """Kelas abstrak yang mendefinisikan kontrak antarmuka polimorfik perhitungan biaya layanan medis."""

    def __init__(self, kode_layanan: str, nama_layanan: str, tarif_dasar: float):
        if tarif_dasar < 0:
            raise ValueError("Tarif dasar layanan tidak boleh bernilai negatif.")
        self._kode_layanan = kode_layanan
        self._nama_layanan = nama_layanan
        self._tarif_dasar = float(tarif_dasar)

    @property
    def kode_layanan(self) -> str:
        return self._kode_layanan

    @property
    def nama_layanan(self) -> str:
        return self._nama_layanan

    @property
    def tarif_dasar(self) -> float:
        return self._tarif_dasar

    @abstractmethod
    def hitung_total_biaya(self) -> float:
        """Menghitung total biaya komponen layanan secara polimorfik."""
        raise NotImplementedError

    def get_deskripsi(self) -> str:
        return f"[{self._kode_layanan}] {self._nama_layanan}"

    def to_dict(self) -> dict:
        return {
            "tipe_layanan": self.__class__.__name__,
            "kode_layanan": self._kode_layanan,
            "nama_layanan": self._nama_layanan,
            "tarif_dasar": self._tarif_dasar,
            "total_biaya": self.hitung_total_biaya(),
            "deskripsi": self.get_deskripsi(),
        }


class KonsultasiDokter(LayananKlinik):
    """Sub-kelas konkret untuk kalkulasi tarif konsultasi dokter."""

    def __init__(
        self,
        kode: str,
        nama: str,
        tarif_dasar: float,
        tunjangan_spesialis: float = 0.0,
    ):
        super().__init__(kode, nama, tarif_dasar)
        if tunjangan_spesialis < 0:
            raise ValueError("Tunjangan spesialis tidak boleh negatif.")
        self.__tunjangan_spesialis = float(tunjangan_spesialis)

    @property
    def tunjangan_spesialis(self) -> float:
        return self.__tunjangan_spesialis

    def hitung_total_biaya(self) -> float:
        return self._tarif_dasar + self.__tunjangan_spesialis

    def get_deskripsi(self) -> str:
        if self.__tunjangan_spesialis > 0:
            return f"{super().get_deskripsi()} (+ Tunjangan Spesialis)"
        return super().get_deskripsi()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["tunjangan_spesialis"] = self.__tunjangan_spesialis
        return data


class TindakanMedis(LayananKlinik):
    """Sub-kelas konkret untuk kalkulasi tarif tindakan medis + bahan habis pakai."""

    def __init__(
        self,
        kode: str,
        nama: str,
        tarif_dasar: float,
        biaya_alat_habis_pakai: float = 0.0,
    ):
        super().__init__(kode, nama, tarif_dasar)
        if biaya_alat_habis_pakai < 0:
            raise ValueError("Biaya alat habis pakai tidak boleh negatif.")
        self.__biaya_alat_habis_pakai = float(biaya_alat_habis_pakai)

    @property
    def biaya_alat_habis_pakai(self) -> float:
        return self.__biaya_alat_habis_pakai

    def hitung_total_biaya(self) -> float:
        return self._tarif_dasar + self.__biaya_alat_habis_pakai

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["biaya_alat_habis_pakai"] = self.__biaya_alat_habis_pakai
        return data


class PenjualanObat(LayananKlinik):
    """Sub-kelas konkret untuk kalkulasi total harga obat ((harga_satuan * jumlah_beli) + biaya_racik)."""

    def __init__(
        self,
        kode: str,
        nama: str,
        harga_satuan: float,
        jumlah_beli: int,
        biaya_racik: float = 0.0,
    ):
        super().__init__(kode, nama, harga_satuan)
        if jumlah_beli <= 0:
            raise ValueError("Jumlah beli obat harus minimal 1.")
        if biaya_racik < 0:
            raise ValueError("Biaya racik tidak boleh negatif.")
        self.__jumlah_beli = int(jumlah_beli)
        self.__biaya_racik = float(biaya_racik)

    @property
    def jumlah_beli(self) -> int:
        return self.__jumlah_beli

    @property
    def biaya_racik(self) -> float:
        return self.__biaya_racik

    def hitung_total_biaya(self) -> float:
        return (self._tarif_dasar * self.__jumlah_beli) + self.__biaya_racik

    def get_deskripsi(self) -> str:
        racik_info = f" + Racik Rp{self.__biaya_racik:,.0f}" if self.__biaya_racik > 0 else ""
        return f"{super().get_deskripsi()} x{self.__jumlah_beli}{racik_info}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["jumlah_beli"] = self.__jumlah_beli
        data["biaya_racik"] = self.__biaya_racik
        return data
