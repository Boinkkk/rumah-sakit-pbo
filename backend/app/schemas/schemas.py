from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=3, max_length=128)
    peran: str | None = None


class PasienCreate(BaseModel):
    nik: str = Field(..., min_length=16, max_length=16)
    nama: str = Field(..., min_length=2, max_length=120)
    tanggal_lahir: date
    jenis_kelamin: Literal["Laki-laki", "Perempuan"] = "Laki-laki"
    alamat: str = ""
    no_telepon: str = ""
    riwayat_alergi: str = "Tidak ada"

    @field_validator("nik")
    @classmethod
    def validate_nik(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 16:
            raise ValueError("NIK harus terdiri dari 16 digit angka valid.")
        return v

    @field_validator("tanggal_lahir")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Tanggal lahir tidak boleh di masa depan.")
        return v


class PasienUpdate(BaseModel):
    nik: str | None = Field(default=None, min_length=16, max_length=16)
    nama: str | None = Field(default=None, min_length=2, max_length=120)
    tanggal_lahir: date | None = None
    jenis_kelamin: Literal["Laki-laki", "Perempuan"] | None = None
    alamat: str | None = None
    no_telepon: str | None = None
    riwayat_alergi: str | None = None
    aktif: bool | None = None


class AntreanCreate(BaseModel):
    pasien_nomor_rm: str = Field(..., min_length=3, max_length=32)
    poli_tujuan: Literal["Poli Umum", "Poli Gigi", "Poli Anak"] = "Poli Umum"
    prioritas: Literal["Reguler", "Lansia", "Darurat"] = "Reguler"


class TindakanInput(BaseModel):
    kode_layanan: str = Field(..., min_length=2, max_length=32)
    nama_layanan: str = Field(..., min_length=2, max_length=150)
    tarif_dasar: float = Field(..., ge=0)
    biaya_alat_habis_pakai: float = Field(default=0.0, ge=0)


class ResepInput(BaseModel):
    kode_obat: str = Field(..., min_length=2, max_length=32)
    jumlah_beli: int = Field(..., ge=1)
    dosis: str = Field(default="3x1 sesudah makan", min_length=2, max_length=120)
    biaya_racik: float = Field(default=0.0, ge=0)


class RekamMedisCreate(BaseModel):
    pasien_nomor_rm: str = Field(..., min_length=3, max_length=32)
    antrean_id: int | None = None
    keluhan_utama: str = Field(..., min_length=3)
    tekanan_darah: str = Field(default="120/80 mmHg", min_length=3, max_length=32)
    suhu_tubuh: float = Field(default=36.5, ge=30.0, le=45.0)
    denyut_nadi: int = Field(default=80, ge=30, le=220)
    diagnosis: str = Field(..., min_length=2, max_length=255)
    catatan_dokter: str = ""
    tindakan: list[TindakanInput] = Field(default_factory=list)
    resep: list[ResepInput] = Field(default_factory=list)


class ObatCreate(BaseModel):
    kode_obat: str | None = None
    nama_obat: str = Field(..., min_length=2, max_length=120)
    stok: int = Field(..., ge=0)
    harga_satuan: float = Field(..., ge=0)
    satuan: str = "Tablet"
    kategori: str = "Umum"


class ObatUpdate(BaseModel):
    nama_obat: str | None = Field(default=None, min_length=2, max_length=120)
    stok: int | None = Field(default=None, ge=0)
    harga_satuan: float | None = Field(default=None, ge=0)
    satuan: str | None = None
    kategori: str | None = None


class PembayaranRequest(BaseModel):
    nominal_bayar: float = Field(..., gt=0)
    metode_pembayaran: Literal["Tunai", "Nontunai"] = "Tunai"


class PublicAntreanPasienLamaRequest(BaseModel):
    identitas: str = Field(..., min_length=3, max_length=32, description="NIK 16 digit atau Nomor RM")
    tanggal_lahir: date
    poli_tujuan: Literal["Poli Umum", "Poli Gigi", "Poli Anak"] = "Poli Umum"


class PublicAntreanPasienBaruRequest(BaseModel):
    nik: str = Field(..., min_length=16, max_length=16)
    nama: str = Field(..., min_length=2, max_length=120)
    tanggal_lahir: date
    jenis_kelamin: Literal["Laki-laki", "Perempuan"] = "Laki-laki"
    alamat: str = ""
    no_telepon: str = ""
    riwayat_alergi: str = "Tidak ada"
    poli_tujuan: Literal["Poli Umum", "Poli Gigi", "Poli Anak"] = "Poli Umum"

    @field_validator("nik")
    @classmethod
    def validate_public_nik(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 16:
            raise ValueError("NIK harus terdiri dari 16 digit angka valid.")
        return v

    @field_validator("tanggal_lahir")
    @classmethod
    def validate_public_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Tanggal lahir tidak boleh di masa depan.")
        return v

