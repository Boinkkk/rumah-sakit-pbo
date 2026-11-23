from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    AntreanModel,
    ObatModel,
    PenggunaModel,
    RekamMedisModel,
    TransaksiPembayaranModel,
)
from app.domain.enums import PeranPengguna
from app.domain.obat import Obat
from app.domain.pengguna import (
    Dokter,
    Kasir,
    Pengguna,
    PetugasAdministrasi,
    PetugasFarmasi,
)


def model_to_pengguna_domain(m: PenggunaModel) -> Pengguna:
    if m.peran == PeranPengguna.DOKTER:
        return Dokter(
            id_pengguna=m.id_pengguna,
            nama_lengkap=m.nama_lengkap,
            username=m.username,
            password_hash=m.password_hash,
            nomor_sip=m.nomor_sip or "-",
            spesialisasi=m.spesialisasi or "Dokter Umum",
            tarif_konsultasi=m.tarif_konsultasi or 50000.0,
            tunjangan_spesialis=m.tunjangan_spesialis or 0.0,
        )
    if m.peran == PeranPengguna.PETUGAS_ADMINISTRASI:
        return PetugasAdministrasi(
            id_pengguna=m.id_pengguna,
            nama_lengkap=m.nama_lengkap,
            username=m.username,
            password_hash=m.password_hash,
            kode_staf=m.kode_staf or "-",
            shift_kerja=m.shift_kerja or "Pagi",
        )
    if m.peran == PeranPengguna.PETUGAS_FARMASI:
        return PetugasFarmasi(
            id_pengguna=m.id_pengguna,
            nama_lengkap=m.nama_lengkap,
            username=m.username,
            password_hash=m.password_hash,
            nomor_strttk=m.nomor_strttk or "-",
        )
    if m.peran == PeranPengguna.KASIR:
        return Kasir(
            id_pengguna=m.id_pengguna,
            nama_lengkap=m.nama_lengkap,
            username=m.username,
            password_hash=m.password_hash,
            nomor_loket=m.nomor_loket or "Loket 01",
        )
    raise ValueError(f"Peran pengguna tidak dikenali: {m.peran}")


def model_to_obat_domain(m: ObatModel) -> Obat:
    return Obat(
        kode_obat=m.kode_obat,
        nama_obat=m.nama_obat,
        stok=m.stok,
        harga_satuan=m.harga_satuan,
        satuan=m.satuan,
        kategori=m.kategori,
    )


class PenggunaRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_username(self, username: str) -> PenggunaModel | None:
        res = await self._session.execute(
            select(PenggunaModel).where(PenggunaModel.username == username.strip())
        )
        return res.scalar_one_or_none()

    async def get_by_id(self, id_pengguna: str) -> PenggunaModel | None:
        res = await self._session.execute(
            select(PenggunaModel).where(PenggunaModel.id_pengguna == id_pengguna)
        )
        return res.scalar_one_or_none()

    async def list_dokter(self) -> list[PenggunaModel]:
        res = await self._session.execute(
            select(PenggunaModel).where(PenggunaModel.peran == PeranPengguna.DOKTER)
        )
        return list(res.scalars().all())


class ObatRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, query: str = "") -> list[ObatModel]:
        stmt = select(ObatModel)
        if query.strip():
            q = f"%{query.strip()}%"
            stmt = stmt.where(
                (ObatModel.nama_obat.ilike(q)) | (ObatModel.kode_obat.ilike(q))
            )
        stmt = stmt.order_by(ObatModel.kode_obat.asc())
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_kode(self, kode_obat: str) -> ObatModel | None:
        res = await self._session.execute(
            select(ObatModel).where(ObatModel.kode_obat == kode_obat.strip().upper())
        )
        return res.scalar_one_or_none()

    async def generate_kode_obat(self) -> str:
        res = await self._session.execute(select(func.count()).select_from(ObatModel))
        idx = int(res.scalar_one() or 0) + 1
        while True:
            kode = f"OBT-{idx:03d}"
            if await self.get_by_kode(kode) is None:
                return kode
            idx += 1


class AntreanRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_today(self, poli: str | None = None) -> list[AntreanModel]:
        today_start = datetime.combine(date.today(), datetime.min.time())
        stmt = (
            select(AntreanModel)
            .options(selectinload(AntreanModel.pasien))
            .where(AntreanModel.waktu_daftar >= today_start)
        )
        if poli:
            stmt = stmt.where(AntreanModel.poli_tujuan == poli)
        stmt = stmt.order_by(AntreanModel.waktu_daftar.asc(), AntreanModel.id.asc())
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id(self, antrean_id: int) -> AntreanModel | None:
        res = await self._session.execute(
            select(AntreanModel)
            .options(selectinload(AntreanModel.pasien))
            .where(AntreanModel.id == antrean_id)
        )
        return res.scalar_one_or_none()


class RekamMedisRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_by_pasien(self, nomor_rm: str) -> list[RekamMedisModel]:
        res = await self._session.execute(
            select(RekamMedisModel)
            .options(
                selectinload(RekamMedisModel.tindakan_list),
                selectinload(RekamMedisModel.resep_list),
                selectinload(RekamMedisModel.pasien),
            )
            .where(RekamMedisModel.pasien_nomor_rm == nomor_rm)
            .order_by(RekamMedisModel.created_at.desc())
        )
        return list(res.scalars().all())

    async def list_all(self, status_resep: str | None = None) -> list[RekamMedisModel]:
        stmt = select(RekamMedisModel).options(
            selectinload(RekamMedisModel.tindakan_list),
            selectinload(RekamMedisModel.resep_list),
            selectinload(RekamMedisModel.pasien),
        )
        if status_resep:
            stmt = stmt.where(RekamMedisModel.status_resep == status_resep)
        stmt = stmt.order_by(RekamMedisModel.created_at.desc())
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id(self, id_rekam_medis: str) -> RekamMedisModel | None:
        res = await self._session.execute(
            select(RekamMedisModel)
            .options(
                selectinload(RekamMedisModel.tindakan_list),
                selectinload(RekamMedisModel.resep_list),
                selectinload(RekamMedisModel.pasien),
            )
            .where(RekamMedisModel.id_rekam_medis == id_rekam_medis)
        )
        return res.scalar_one_or_none()

    async def generate_id(self) -> str:
        res = await self._session.execute(select(func.count()).select_from(RekamMedisModel))
        idx = int(res.scalar_one() or 0) + 1
        today_str = date.today().strftime("%Y%m%d")
        while True:
            candidate = f"RMED-{today_str}-{idx:03d}"
            if await self.get_by_id(candidate) is None:
                return candidate
            idx += 1


class TransaksiRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, status_lunas: bool | None = None) -> list[TransaksiPembayaranModel]:
        stmt = select(TransaksiPembayaranModel).options(
            selectinload(TransaksiPembayaranModel.layanan_list)
        )
        if status_lunas is not None:
            stmt = stmt.where(TransaksiPembayaranModel.status_lunas.is_(status_lunas))
        stmt = stmt.order_by(TransaksiPembayaranModel.waktu.desc())
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id(self, id_transaksi: str) -> TransaksiPembayaranModel | None:
        res = await self._session.execute(
            select(TransaksiPembayaranModel)
            .options(selectinload(TransaksiPembayaranModel.layanan_list))
            .where(TransaksiPembayaranModel.id_transaksi == id_transaksi)
        )
        return res.scalar_one_or_none()

    async def get_by_rekam_medis_id(self, rekam_medis_id: str) -> TransaksiPembayaranModel | None:
        res = await self._session.execute(
            select(TransaksiPembayaranModel)
            .options(selectinload(TransaksiPembayaranModel.layanan_list))
            .where(TransaksiPembayaranModel.rekam_medis_id == rekam_medis_id)
        )
        return res.scalar_one_or_none()

    async def generate_id(self) -> str:
        res = await self._session.execute(
            select(func.count()).select_from(TransaksiPembayaranModel)
        )
        idx = int(res.scalar_one() or 0) + 1
        today_str = date.today().strftime("%Y%m%d")
        while True:
            candidate = f"TRX-{today_str}-{idx:03d}"
            if await self.get_by_id(candidate) is None:
                return candidate
            idx += 1
