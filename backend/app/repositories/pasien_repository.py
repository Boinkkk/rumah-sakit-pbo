from __future__ import annotations

from datetime import date
from typing import overload

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PasienModel
from app.domain.pasien import Pasien


def model_to_pasien_domain(m: PasienModel) -> Pasien:
    return Pasien(
        nomor_rm=m.nomor_rm,
        nik=m.nik,
        nama=m.nama,
        tanggal_lahir=m.tanggal_lahir,
        jenis_kelamin=m.jenis_kelamin,
        alamat=m.alamat,
        no_telepon=m.no_telepon,
        riwayat_alergi=m.riwayat_alergi,
        aktif=m.aktif,
    )


class PasienRepository:
    """Repository pasien dengan implementasi Static Polymorphism (Method Overloading) pada cari_pasien."""

    def __init__(self, session: AsyncSession | None = None, items: list[Pasien] | None = None):
        self._session = session
        self._items: list[Pasien] = items or []

    def simpan_memori(self, pasien: Pasien) -> None:
        self._items.append(pasien)

    @overload
    def cari_pasien(self, nomor_rm: str) -> Pasien | None: ...

    @overload
    def cari_pasien(self, nama_lengkap: str, tanggal_lahir: date) -> list[Pasien]: ...

    def cari_pasien(
        self,
        kunci: str,
        tanggal_lahir: date | None = None,
    ) -> Pasien | list[Pasien] | None:
        """
        Method overloading (Static Polymorphism):
        - cari_pasien(nomor_rm) -> pencarian instan berbasis Nomor Rekam Medis.
        - cari_pasien(nama_lengkap, tanggal_lahir) -> pencarian alternatif berdasarkan nama & tanggal lahir.
        """
        if tanggal_lahir is None:
            target = kunci.strip().upper()
            for p in self._items:
                if p.get_nomor_rm().upper() == target:
                    return p
            return None

        target_nama = kunci.strip().lower()
        return [
            p
            for p in self._items
            if target_nama in p.get_nama().lower() and p.get_tanggal_lahir() == tanggal_lahir
        ]

    async def get_by_nomor_rm(self, nomor_rm: str) -> PasienModel | None:
        assert self._session is not None
        res = await self._session.execute(
            select(PasienModel).where(PasienModel.nomor_rm == nomor_rm)
        )
        return res.scalar_one_or_none()

    async def get_by_nik(self, nik: str) -> PasienModel | None:
        assert self._session is not None
        res = await self._session.execute(select(PasienModel).where(PasienModel.nik == nik))
        return res.scalar_one_or_none()

    async def search_db(
        self,
        query: str = "",
        tanggal_lahir: date | None = None,
        include_inactive: bool = False,
    ) -> list[PasienModel]:
        assert self._session is not None
        stmt = select(PasienModel)
        if not include_inactive:
            stmt = stmt.where(PasienModel.aktif.is_(True))
        if query.strip():
            q = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    PasienModel.nomor_rm.ilike(q),
                    PasienModel.nik.ilike(q),
                    PasienModel.nama.ilike(q),
                )
            )
        if tanggal_lahir is not None:
            stmt = stmt.where(PasienModel.tanggal_lahir == tanggal_lahir)
        stmt = stmt.order_by(PasienModel.created_at.desc())
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def generate_nomor_rm(self) -> str:
        assert self._session is not None
        res = await self._session.execute(select(func.count()).select_from(PasienModel))
        count = int(res.scalar_one() or 0) + 1
        year = date.today().year
        while True:
            candidate = f"RM-{year}-{count:04d}"
            existing = await self.get_by_nomor_rm(candidate)
            if existing is None:
                return candidate
            count += 1
