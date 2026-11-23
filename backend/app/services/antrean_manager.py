from __future__ import annotations

from datetime import date, datetime
from typing import overload

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AntreanModel
from app.domain.enums import JenisPoli, StatusAntrean, TingkatUrgensi
from app.domain.operasional import Antrean
from app.domain.pasien import Pasien
from app.repositories.clinic_repositories import AntreanRepository
from app.repositories.pasien_repository import PasienRepository

POLI_PREFIX = {
    JenisPoli.POLI_UMUM: "A",
    JenisPoli.POLI_GIGI: "G",
    JenisPoli.POLI_ANAK: "K",
}

PRIORITAS_WEIGHT = {
    TingkatUrgensi.DARURAT: 0,
    TingkatUrgensi.LANSIA: 1,
    TingkatUrgensi.REGULER: 2,
}


class AntreanManager:
    """
    Service Engine pengelola antrean FIFO + Prioritas (Aggregation dengan Antrean).
    Mendemonstrasikan Static Polymorphism (Method Overloading) pada tambah_antrean.
    """

    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._antrean_memori: list[Antrean] = []
        self._counters: dict[str, int] = {"A": 0, "G": 0, "K": 0}

    @overload
    def tambah_antrean(self, pasien: Pasien) -> Antrean: ...

    @overload
    def tambah_antrean(
        self,
        pasien: Pasien,
        prioritas: TingkatUrgensi | str,
        poli_tujuan: str = JenisPoli.POLI_UMUM,
    ) -> Antrean: ...

    def tambah_antrean(
        self,
        pasien: Pasien,
        prioritas: TingkatUrgensi | str | None = None,
        poli_tujuan: str = JenisPoli.POLI_UMUM,
    ) -> Antrean:
        """
        Method overloading (Static Polymorphism):
        - tambah_antrean(pasien) -> pendaftaran antrean reguler pada Poli Umum.
        - tambah_antrean(pasien, prioritas, poli_tujuan) -> antrean dengan tingkat urgensi (Darurat/Lansia).
        """
        tingkat = str(prioritas) if prioritas is not None else TingkatUrgensi.REGULER
        prefix = POLI_PREFIX.get(poli_tujuan, "A")
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        nomor = f"{prefix}-{self._counters[prefix]:03d}"

        antrean = Antrean(
            nomor_antrean=nomor,
            poli_tujuan=poli_tujuan,
            pasien_nomor_rm=pasien.get_nomor_rm(),
            pasien_nama=pasien.get_nama(),
            prioritas=tingkat,
            status=StatusAntrean.MENUNGGU,
        )
        self._antrean_memori.append(antrean)
        return antrean

    def panggil_berikutnya_memori(self, poli_tujuan: str | None = None) -> Antrean | None:
        kandidat = [
            a
            for a in self._antrean_memori
            if a.get_status() == StatusAntrean.MENUNGGU
            and (poli_tujuan is None or a.get_poli_tujuan() == poli_tujuan)
        ]
        if not kandidat:
            return None
        kandidat.sort(
            key=lambda a: (
                PRIORITAS_WEIGHT.get(a.get_prioritas(), 2),
                a.get_waktu_daftar(),
            )
        )
        terpilih = kandidat[0]
        terpilih.panggil()
        return terpilih

    def get_daftar_antrean_memori(self) -> list[Antrean]:
        return list(self._antrean_memori)

    async def daftar_antrean_db(
        self,
        pasien_nomor_rm: str,
        poli_tujuan: str,
        prioritas: str = TingkatUrgensi.REGULER,
    ) -> AntreanModel:
        assert self._session is not None
        pasien_repo = PasienRepository(self._session)
        pasien = await pasien_repo.get_by_nomor_rm(pasien_nomor_rm)
        if pasien is None:
            raise ValueError(f"Pasien dengan NRM '{pasien_nomor_rm}' tidak ditemukan.")
        if not pasien.aktif:
            raise ValueError(f"Pasien '{pasien.nama}' berstatus nonaktif.")

        prefix = POLI_PREFIX.get(poli_tujuan, "A")
        today_start = datetime.combine(date.today(), datetime.min.time())
        res = await self._session.execute(
            select(func.count())
            .select_from(AntreanModel)
            .where(
                AntreanModel.poli_tujuan == poli_tujuan,
                AntreanModel.waktu_daftar >= today_start,
            )
        )
        count = int(res.scalar_one() or 0) + 1
        nomor_antrean = f"{prefix}-{count:03d}"

        antrean_model = AntreanModel(
            nomor_antrean=nomor_antrean,
            pasien_nomor_rm=pasien.nomor_rm,
            poli_tujuan=poli_tujuan,
            prioritas=prioritas,
            status=StatusAntrean.MENUNGGU,
            waktu_daftar=datetime.now(),
        )
        self._session.add(antrean_model)
        await self._session.commit()
        await self._session.refresh(antrean_model)
        repo = AntreanRepository(self._session)
        loaded = await repo.get_by_id(antrean_model.id)
        assert loaded is not None
        return loaded

    async def find_active_antrean_today_db(self, pasien_nomor_rm: str) -> AntreanModel | None:
        """Mencari antrean aktif (Menunggu/Diperiksa) milik pasien pada hari ini."""
        assert self._session is not None
        repo = AntreanRepository(self._session)
        items = await repo.list_today()
        for item in items:
            if (
                item.pasien_nomor_rm == pasien_nomor_rm
                and item.status in (StatusAntrean.MENUNGGU, StatusAntrean.DIPERIKSA)
            ):
                return item
        return None

    async def count_ahead_in_poli_db(self, target: AntreanModel) -> int:
        """Menghitung jumlah pasien yang berada di depan target pada poli yang sama."""
        assert self._session is not None
        if target.status != StatusAntrean.MENUNGGU:
            return 0
        repo = AntreanRepository(self._session)
        items = await repo.list_today(poli=target.poli_tujuan)
        menunggu = [i for i in items if i.status == StatusAntrean.MENUNGGU]
        menunggu.sort(
            key=lambda a: (
                PRIORITAS_WEIGHT.get(a.prioritas, 2),
                a.waktu_daftar,
                a.id,
            )
        )
        for idx, item in enumerate(menunggu):
            if item.id == target.id:
                return idx
        return 0

    async def panggil_berikutnya_db(self, poli_tujuan: str | None = None) -> AntreanModel:
        assert self._session is not None
        repo = AntreanRepository(self._session)
        items = await repo.list_today(poli=poli_tujuan)

        # Cek apakah ada pasien yang masih berstatus Diperiksa di poli tersebut
        sedang_diperiksa = [i for i in items if i.status == StatusAntrean.DIPERIKSA]
        if sedang_diperiksa:
            raise ValueError(
                f"Masih ada pasien ({sedang_diperiksa[0].nomor_antrean} - {sedang_diperiksa[0].pasien.nama}) yang sedang diperiksa."
            )

        menunggu = [i for i in items if i.status == StatusAntrean.MENUNGGU]
        if not menunggu:
            raise ValueError("Tidak ada antrean pasien yang sedang menunggu.")

        menunggu.sort(
            key=lambda a: (
                PRIORITAS_WEIGHT.get(a.prioritas, 2),
                a.waktu_daftar,
                a.id,
            )
        )
        berikutnya = menunggu[0]
        domain_obj = Antrean(
            nomor_antrean=berikutnya.nomor_antrean,
            poli_tujuan=berikutnya.poli_tujuan,
            pasien_nomor_rm=berikutnya.pasien_nomor_rm,
            pasien_nama=berikutnya.pasien.nama if berikutnya.pasien else "",
            prioritas=berikutnya.prioritas,
            status=berikutnya.status,
            waktu_daftar=berikutnya.waktu_daftar,
        )
        domain_obj.panggil()

        berikutnya.status = domain_obj.get_status()
        berikutnya.waktu_panggil = datetime.now()
        await self._session.commit()
        await self._session.refresh(berikutnya)
        return berikutnya
