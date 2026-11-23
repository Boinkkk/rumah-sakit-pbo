from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class PenggunaModel(Base):
    __tablename__ = "pengguna"

    id_pengguna: Mapped[str] = mapped_column(String(32), primary_key=True)
    nama_lengkap: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    peran: Mapped[str] = mapped_column(String(40), nullable=False)
    # Atribut spesifik sub-kelas Pengguna
    nomor_sip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    spesialisasi: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tarif_konsultasi: Mapped[float | None] = mapped_column(Float, nullable=True)
    tunjangan_spesialis: Mapped[float | None] = mapped_column(Float, nullable=True)
    poli_praktik: Mapped[str | None] = mapped_column(String(40), nullable=True)
    kode_staf: Mapped[str | None] = mapped_column(String(40), nullable=True)
    shift_kerja: Mapped[str | None] = mapped_column(String(40), nullable=True)
    nomor_strttk: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nomor_loket: Mapped[str | None] = mapped_column(String(32), nullable=True)


class PasienModel(Base):
    __tablename__ = "pasien"

    nomor_rm: Mapped[str] = mapped_column(String(32), primary_key=True)
    nik: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    tanggal_lahir: Mapped[date] = mapped_column(Date, nullable=False)
    jenis_kelamin: Mapped[str] = mapped_column(String(20), nullable=False, default="Laki-laki")
    alamat: Mapped[str] = mapped_column(Text, nullable=False, default="")
    no_telepon: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    riwayat_alergi: Mapped[str] = mapped_column(Text, nullable=False, default="Tidak ada")
    aktif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    antrean_list: Mapped[list["AntreanModel"]] = relationship(
        back_populates="pasien", cascade="all, delete-orphan"
    )
    rekam_medis_list: Mapped[list["RekamMedisModel"]] = relationship(
        back_populates="pasien", cascade="all, delete-orphan"
    )


class ObatModel(Base):
    __tablename__ = "obat"

    kode_obat: Mapped[str] = mapped_column(String(32), primary_key=True)
    nama_obat: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    stok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    harga_satuan: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    satuan: Mapped[str] = mapped_column(String(32), nullable=False, default="Tablet")
    kategori: Mapped[str] = mapped_column(String(64), nullable=False, default="Umum")


class AntreanModel(Base):
    __tablename__ = "antrean"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nomor_antrean: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    pasien_nomor_rm: Mapped[str] = mapped_column(
        String(32), ForeignKey("pasien.nomor_rm", ondelete="CASCADE"), nullable=False
    )
    poli_tujuan: Mapped[str] = mapped_column(String(40), nullable=False)
    prioritas: Mapped[str] = mapped_column(String(20), nullable=False, default="Reguler")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Menunggu")
    waktu_daftar: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    waktu_panggil: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    pasien: Mapped[PasienModel] = relationship(back_populates="antrean_list")


class RekamMedisModel(Base):
    __tablename__ = "rekam_medis"

    id_rekam_medis: Mapped[str] = mapped_column(String(32), primary_key=True)
    pasien_nomor_rm: Mapped[str] = mapped_column(
        String(32), ForeignKey("pasien.nomor_rm", ondelete="CASCADE"), nullable=False
    )
    dokter_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("pengguna.id_pengguna"), nullable=False
    )
    antrean_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("antrean.id"), nullable=True
    )
    tanggal_periksa: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    keluhan_utama: Mapped[str] = mapped_column(Text, nullable=False)
    tekanan_darah: Mapped[str] = mapped_column(String(32), nullable=False, default="120/80 mmHg")
    suhu_tubuh: Mapped[float] = mapped_column(Float, nullable=False, default=36.5)
    denyut_nadi: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    diagnosis: Mapped[str] = mapped_column(String(255), nullable=False)
    catatan_dokter: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status_resep: Mapped[str] = mapped_column(
        String(32), nullable=False, default="Menunggu Validasi"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    pasien: Mapped[PasienModel] = relationship(back_populates="rekam_medis_list")
    tindakan_list: Mapped[list["DetailTindakanModel"]] = relationship(
        back_populates="rekam_medis", cascade="all, delete-orphan"
    )
    resep_list: Mapped[list["DetailResepModel"]] = relationship(
        back_populates="rekam_medis", cascade="all, delete-orphan"
    )


class DetailTindakanModel(Base):
    __tablename__ = "detail_tindakan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rekam_medis_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("rekam_medis.id_rekam_medis", ondelete="CASCADE"), nullable=False
    )
    kode_layanan: Mapped[str] = mapped_column(String(32), nullable=False)
    nama_layanan: Mapped[str] = mapped_column(String(150), nullable=False)
    tarif_dasar: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    biaya_alat_habis_pakai: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    rekam_medis: Mapped[RekamMedisModel] = relationship(back_populates="tindakan_list")


class DetailResepModel(Base):
    __tablename__ = "detail_resep"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rekam_medis_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("rekam_medis.id_rekam_medis", ondelete="CASCADE"), nullable=False
    )
    kode_obat: Mapped[str] = mapped_column(
        String(32), ForeignKey("obat.kode_obat"), nullable=False
    )
    nama_obat: Mapped[str] = mapped_column(String(120), nullable=False)
    jumlah_beli: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dosis: Mapped[str] = mapped_column(String(120), nullable=False, default="3x1 sesudah makan")
    harga_satuan: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    biaya_racik: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tervalidasi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    rekam_medis: Mapped[RekamMedisModel] = relationship(back_populates="resep_list")


class TransaksiPembayaranModel(Base):
    __tablename__ = "transaksi_pembayaran"

    id_transaksi: Mapped[str] = mapped_column(String(32), primary_key=True)
    pasien_nomor_rm: Mapped[str] = mapped_column(
        String(32), ForeignKey("pasien.nomor_rm"), nullable=False
    )
    rekam_medis_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("rekam_medis.id_rekam_medis"), unique=True, nullable=False
    )
    kasir_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("pengguna.id_pengguna"), nullable=True
    )
    waktu: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    grand_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nominal_bayar: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    kembalian: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metode_pembayaran: Mapped[str] = mapped_column(String(32), nullable=False, default="Tunai")
    status_lunas: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    layanan_list: Mapped[list["DetailLayananTransaksiModel"]] = relationship(
        back_populates="transaksi", cascade="all, delete-orphan"
    )


class DetailLayananTransaksiModel(Base):
    __tablename__ = "detail_layanan_transaksi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaksi_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("transaksi_pembayaran.id_transaksi", ondelete="CASCADE"),
        nullable=False,
    )
    tipe_layanan: Mapped[str] = mapped_column(String(40), nullable=False)
    kode_layanan: Mapped[str] = mapped_column(String(32), nullable=False)
    nama_layanan: Mapped[str] = mapped_column(String(150), nullable=False)
    tarif_dasar: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    biaya_tambahan: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    jumlah: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    transaksi: Mapped[TransaksiPembayaranModel] = relationship(back_populates="layanan_list")
