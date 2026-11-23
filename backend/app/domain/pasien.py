from __future__ import annotations

from datetime import date
import re


class Pasien:
    """Entitas Pasien dengan enkapsulasi ketat pada atribut identitas dan tanggal lahir."""

    def __init__(
        self,
        nomor_rm: str,
        nik: str,
        nama: str,
        tanggal_lahir: date,
        jenis_kelamin: str = "Laki-laki",
        alamat: str = "",
        no_telepon: str = "",
        riwayat_alergi: str = "Tidak ada",
        aktif: bool = True,
    ):
        self.__nomor_rm = ""
        self.__nik = ""
        self.__nama = ""
        self.__tanggal_lahir = date.today()
        self.__jenis_kelamin = "Laki-laki"
        self.__alamat = ""
        self.__no_telepon = ""
        self.__riwayat_alergi = "Tidak ada"
        self.__aktif = aktif

        self.set_nomor_rm(nomor_rm)
        self.set_nik(nik)
        self.set_nama(nama)
        self.set_tanggal_lahir(tanggal_lahir)
        self.set_jenis_kelamin(jenis_kelamin)
        self.set_alamat(alamat)
        self.set_no_telepon(no_telepon)
        self.set_riwayat_alergi(riwayat_alergi)

    def get_nomor_rm(self) -> str:
        return self.__nomor_rm

    def set_nomor_rm(self, nomor_rm: str) -> None:
        if not nomor_rm or not nomor_rm.strip():
            raise ValueError("Nomor Rekam Medis (NRM) tidak boleh kosong.")
        self.__nomor_rm = nomor_rm.strip()

    def get_nik(self) -> str:
        return self.__nik

    def set_nik(self, nik: str) -> None:
        if nik is None or len(nik) != 16 or not nik.isdigit():
            raise ValueError("NIK harus terdiri dari 16 digit angka valid.")
        self.__nik = nik

    def get_nama(self) -> str:
        return self.__nama

    def set_nama(self, nama: str) -> None:
        if not nama or len(nama.strip()) < 2:
            raise ValueError("Nama pasien minimal terdiri dari 2 karakter.")
        self.__nama = nama.strip()

    def get_tanggal_lahir(self) -> date:
        return self.__tanggal_lahir

    def set_tanggal_lahir(self, tanggal_lahir: date) -> None:
        if tanggal_lahir is None:
            raise ValueError("Tanggal lahir wajib diisi.")
        if tanggal_lahir > date.today():
            raise ValueError("Tanggal lahir tidak boleh di masa depan.")
        self.__tanggal_lahir = tanggal_lahir

    def get_jenis_kelamin(self) -> str:
        return self.__jenis_kelamin

    def set_jenis_kelamin(self, jenis_kelamin: str) -> None:
        normalized = (jenis_kelamin or "").strip()
        if normalized not in ("Laki-laki", "Perempuan"):
            raise ValueError("Jenis kelamin harus 'Laki-laki' atau 'Perempuan'.")
        self.__jenis_kelamin = normalized

    def get_alamat(self) -> str:
        return self.__alamat

    def set_alamat(self, alamat: str) -> None:
        self.__alamat = (alamat or "").strip()

    def get_no_telepon(self) -> str:
        return self.__no_telepon

    def set_no_telepon(self, no_telepon: str) -> None:
        cleaned = (no_telepon or "").strip()
        if cleaned and not re.fullmatch(r"[0-9+\-\s]{8,20}", cleaned):
            raise ValueError("Format nomor telepon tidak valid.")
        self.__no_telepon = cleaned

    def get_riwayat_alergi(self) -> str:
        return self.__riwayat_alergi

    def set_riwayat_alergi(self, riwayat_alergi: str) -> None:
        cleaned = (riwayat_alergi or "").strip()
        self.__riwayat_alergi = cleaned if cleaned else "Tidak ada"

    def is_aktif(self) -> bool:
        return self.__aktif

    def nonaktifkan(self) -> None:
        self.__aktif = False

    def aktifkan(self) -> None:
        self.__aktif = True

    def hitung_umur(self) -> int:
        hari_ini = date.today()
        return hari_ini.year - self.__tanggal_lahir.year - (
            (hari_ini.month, hari_ini.day)
            < (self.__tanggal_lahir.month, self.__tanggal_lahir.day)
        )

    def to_dict(self) -> dict:
        return {
            "nomor_rm": self.__nomor_rm,
            "nik": self.__nik,
            "nama": self.__nama,
            "tanggal_lahir": self.__tanggal_lahir.isoformat(),
            "umur": self.hitung_umur(),
            "jenis_kelamin": self.__jenis_kelamin,
            "alamat": self.__alamat,
            "no_telepon": self.__no_telepon,
            "riwayat_alergi": self.__riwayat_alergi,
            "aktif": self.__aktif,
        }
