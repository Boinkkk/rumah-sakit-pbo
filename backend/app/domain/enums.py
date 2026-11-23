from __future__ import annotations

from enum import StrEnum


class PeranPengguna(StrEnum):
    PETUGAS_ADMINISTRASI = "PetugasAdministrasi"
    DOKTER = "Dokter"
    PETUGAS_FARMASI = "PetugasFarmasi"
    KASIR = "Kasir"


class JenisPoli(StrEnum):
    POLI_UMUM = "Poli Umum"
    POLI_GIGI = "Poli Gigi"
    POLI_ANAK = "Poli Anak"


class StatusAntrean(StrEnum):
    MENUNGGU = "Menunggu"
    DIPERIKSA = "Diperiksa"
    SELESAI_DIPERIKSA = "Selesai Diperiksa"
    SELESAI = "Selesai"


class TingkatUrgensi(StrEnum):
    REGULER = "Reguler"
    LANSIA = "Lansia"
    DARURAT = "Darurat"


class MetodePembayaran(StrEnum):
    TUNAI = "Tunai"
    NONTUNAI = "Nontunai"


class StatusResep(StrEnum):
    MENUNGGU_VALIDASI = "Menunggu Validasi"
    DIVALIDASI = "Divalidasi"
