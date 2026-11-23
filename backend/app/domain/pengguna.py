from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.security import verify_password_sha256
from app.domain.enums import PeranPengguna, TingkatUrgensi
from app.domain.layanan import TindakanMedis
from app.domain.obat import Obat
from app.domain.operasional import Antrean, RekamMedis, TransaksiPembayaran
from app.domain.pasien import Pasien


class Pengguna(ABC):
    """Kelas abstrak super-class yang mendefinisikan karakteristik dasar seluruh staf klinik."""

    def __init__(
        self,
        id_pengguna: str,
        nama_lengkap: str,
        username: str,
        password_hash: str,
        peran: str,
    ):
        self._id_pengguna = id_pengguna
        self._nama_lengkap = nama_lengkap
        self._username = username
        self._password_hash = password_hash
        self._peran = peran

    @property
    def id_pengguna(self) -> str:
        return self._id_pengguna

    @property
    def nama_lengkap(self) -> str:
        return self._nama_lengkap

    @property
    def username(self) -> str:
        return self._username

    @property
    def peran(self) -> str:
        return self._peran

    def verifikasi_login(self, pwd: str) -> bool:
        return verify_password_sha256(pwd, self._password_hash)

    @abstractmethod
    def get_profil(self) -> str:
        """Mengembalikan ringkasan profil staf sesuai perannya."""
        raise NotImplementedError

    def to_dict(self) -> dict:
        return {
            "id_pengguna": self._id_pengguna,
            "nama_lengkap": self._nama_lengkap,
            "username": self._username,
            "peran": self._peran,
            "profil": self.get_profil(),
        }


class Dokter(Pengguna):
    """Sub-kelas Dokter dengan spesialisasi, nomor SIP, dan tarif konsultasi."""

    def __init__(
        self,
        id_pengguna: str,
        nama_lengkap: str,
        username: str,
        password_hash: str,
        nomor_sip: str,
        spesialisasi: str,
        tarif_konsultasi: float,
        tunjangan_spesialis: float = 0.0,
    ):
        super().__init__(
            id_pengguna=id_pengguna,
            nama_lengkap=nama_lengkap,
            username=username,
            password_hash=password_hash,
            peran=PeranPengguna.DOKTER,
        )
        self.__nomor_sip = nomor_sip
        self.__spesialisasi = spesialisasi
        self.__tarif_konsultasi = float(tarif_konsultasi)
        self.__tunjangan_spesialis = float(tunjangan_spesialis)

    @property
    def nomor_sip(self) -> str:
        return self.__nomor_sip

    @property
    def spesialisasi(self) -> str:
        return self.__spesialisasi

    @property
    def tarif_konsultasi(self) -> float:
        return self.__tarif_konsultasi

    @property
    def tunjangan_spesialis(self) -> float:
        return self.__tunjangan_spesialis

    def get_profil(self) -> str:
        return f"{self._nama_lengkap} | {self.__spesialisasi} (SIP: {self.__nomor_sip})"

    def periksa_pasien(
        self,
        p: Pasien,
        id_rekam_medis: str,
        keluhan_utama: str,
        diagnosis: str,
        tekanan_darah: str = "120/80 mmHg",
        suhu_tubuh: float = 36.5,
        denyut_nadi: int = 80,
        tindakan: list[TindakanMedis] | None = None,
    ) -> RekamMedis:
        rm = RekamMedis(
            id_rekam_medis=id_rekam_medis,
            pasien_nomor_rm=p.get_nomor_rm(),
            dokter_id=self._id_pengguna,
            keluhan_utama=keluhan_utama,
            diagnosis=diagnosis,
            tekanan_darah=tekanan_darah,
            suhu_tubuh=suhu_tubuh,
            denyut_nadi=denyut_nadi,
        )
        if tindakan:
            for item in tindakan:
                rm.tambah_tindakan(item)
        return rm

    def buat_resep(
        self,
        rm: RekamMedis,
        daftar_obat: list[tuple[Obat, int, str, float]],
    ) -> None:
        for obat, jumlah, dosis, biaya_racik in daftar_obat:
            rm.tambah_resep(obat, jumlah=jumlah, dosis=dosis, biaya_racik=biaya_racik)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(
            {
                "nomor_sip": self.__nomor_sip,
                "spesialisasi": self.__spesialisasi,
                "tarif_konsultasi": self.__tarif_konsultasi,
                "tunjangan_spesialis": self.__tunjangan_spesialis,
            }
        )
        return data


class PetugasAdministrasi(Pengguna):
    """Sub-kelas PetugasAdministrasi (Resepsionis) untuk pendaftaran dan antrean."""

    def __init__(
        self,
        id_pengguna: str,
        nama_lengkap: str,
        username: str,
        password_hash: str,
        kode_staf: str,
        shift_kerja: str,
    ):
        super().__init__(
            id_pengguna=id_pengguna,
            nama_lengkap=nama_lengkap,
            username=username,
            password_hash=password_hash,
            peran=PeranPengguna.PETUGAS_ADMINISTRASI,
        )
        self.__kode_staf = kode_staf
        self.__shift_kerja = shift_kerja

    @property
    def kode_staf(self) -> str:
        return self.__kode_staf

    @property
    def shift_kerja(self) -> str:
        return self.__shift_kerja

    def get_profil(self) -> str:
        return f"{self._nama_lengkap} | Resepsionis ({self.__kode_staf} - Shift {self.__shift_kerja})"

    def terbitkan_antrean(
        self,
        p: Pasien,
        poli: str,
        nomor_antrean: str,
        prioritas: str = TingkatUrgensi.REGULER,
    ) -> Antrean:
        return Antrean(
            nomor_antrean=nomor_antrean,
            poli_tujuan=poli,
            pasien_nomor_rm=p.get_nomor_rm(),
            pasien_nama=p.get_nama(),
            prioritas=prioritas,
        )

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"kode_staf": self.__kode_staf, "shift_kerja": self.__shift_kerja})
        return data


class PetugasFarmasi(Pengguna):
    """Sub-kelas PetugasFarmasi untuk validasi resep digital dan pengelolaan stok obat."""

    def __init__(
        self,
        id_pengguna: str,
        nama_lengkap: str,
        username: str,
        password_hash: str,
        nomor_strttk: str,
    ):
        super().__init__(
            id_pengguna=id_pengguna,
            nama_lengkap=nama_lengkap,
            username=username,
            password_hash=password_hash,
            peran=PeranPengguna.PETUGAS_FARMASI,
        )
        self.__nomor_strttk = nomor_strttk

    @property
    def nomor_strttk(self) -> str:
        return self.__nomor_strttk

    def get_profil(self) -> str:
        return f"{self._nama_lengkap} | Farmasi (STRTTK: {self.__nomor_strttk})"

    def validasi_resep(self, rm: RekamMedis) -> None:
        for item in rm.get_daftar_resep():
            item.obat.kurangi_stok(item.jumlah)
        rm.set_status_resep("Divalidasi")

    def update_stok_obat(self, o: Obat, jumlah: int) -> None:
        o.set_stok(jumlah)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"nomor_strttk": self.__nomor_strttk})
        return data


class Kasir(Pengguna):
    """Sub-kelas Kasir untuk verifikasi tagihan layanan dan pemrosesan pembayaran."""

    def __init__(
        self,
        id_pengguna: str,
        nama_lengkap: str,
        username: str,
        password_hash: str,
        nomor_loket: str,
    ):
        super().__init__(
            id_pengguna=id_pengguna,
            nama_lengkap=nama_lengkap,
            username=username,
            password_hash=password_hash,
            peran=PeranPengguna.KASIR,
        )
        self.__nomor_loket = nomor_loket

    @property
    def nomor_loket(self) -> str:
        return self.__nomor_loket

    def get_profil(self) -> str:
        return f"{self._nama_lengkap} | Kasir (Loket {self.__nomor_loket})"

    def proses_transaksi(
        self,
        t: TransaksiPembayaran,
        nominal_bayar: float,
        metode_pembayaran: str = "Tunai",
    ) -> float:
        return t.proses_pembayaran(nominal_bayar, metode_pembayaran)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"nomor_loket": self.__nomor_loket})
        return data
