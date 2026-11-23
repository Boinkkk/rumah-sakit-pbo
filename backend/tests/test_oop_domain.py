from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.core.security import hash_password_sha256
from app.domain import (
    Antrean,
    Dokter,
    JenisPoli,
    Kasir,
    KonsultasiDokter,
    LayananKlinik,
    Obat,
    Pasien,
    Pengguna,
    PenjualanObat,
    PetugasAdministrasi,
    PetugasFarmasi,
    RekamMedis,
    StatusAntrean,
    TindakanMedis,
    TingkatUrgensi,
    TransaksiPembayaran,
)
from app.repositories.pasien_repository import PasienRepository
from app.services.antrean_manager import AntreanManager


def test_encapsulation_pasien_validation():
    # NIK harus 16 digit angka
    with pytest.raises(ValueError, match="16 digit"):
        Pasien("RM-001", "12345", "Budi", date(1995, 1, 1))

    with pytest.raises(ValueError, match="16 digit"):
        Pasien("RM-001", "352601120592000A", "Budi", date(1995, 1, 1))

    # Tanggal lahir tidak boleh di masa depan
    besok = date.today() + timedelta(days=1)
    with pytest.raises(ValueError, match="masa depan"):
        Pasien("RM-001", "3526011205920001", "Budi", besok)

    p = Pasien("RM-001", "3526011205920001", "Budi Santoso", date(1992, 5, 12))
    assert p.get_nomor_rm() == "RM-001"
    assert p.hitung_umur() >= 30


def test_encapsulation_obat_non_negatif():
    with pytest.raises(ValueError, match="negatif"):
        Obat("OBT-1", "Paracetamol", -5, 3500)

    with pytest.raises(ValueError, match="negatif"):
        Obat("OBT-1", "Paracetamol", 10, -100)

    obat = Obat("OBT-1", "Paracetamol", 10, 3500)
    obat.kurangi_stok(3)
    assert obat.get_stok() == 7

    with pytest.raises(ValueError, match="tidak mencukupi"):
        obat.kurangi_stok(20)


def test_inheritance_and_sha256_auth():
    # Kelas abstrak tidak dapat diinstansiasi langsung
    with pytest.raises(TypeError):
        Pengguna("U1", "Test", "test", "hash", "Dokter")  # type: ignore[abstract]

    pwd_hash = hash_password_sha256("medika123")
    dokter = Dokter(
        "D1", "dr. Indah", "dokter", pwd_hash, "SIP-01", "Dokter Umum", 50000
    )
    adm = PetugasAdministrasi("A1", "Nadia", "admin", pwd_hash, "ADM-01", "Pagi")
    frm = PetugasFarmasi("F1", "Rizky", "farmasi", pwd_hash, "STRTTK-01")
    ksr = Kasir("K1", "Sinta", "kasir", pwd_hash, "Loket 01")

    assert dokter.verifikasi_login("medika123") is True
    assert dokter.verifikasi_login("salah") is False
    assert "SIP-01" in dokter.get_profil()
    assert "ADM-01" in adm.get_profil()
    assert "STRTTK-01" in frm.get_profil()
    assert "Loket 01" in ksr.get_profil()


def test_dynamic_polymorphism_layanan_dan_transaksi():
    with pytest.raises(TypeError):
        LayananKlinik("L1", "Abstrak", 1000)  # type: ignore[abstract]

    trx = TransaksiPembayaran("TRX-001", pasien_nomor_rm="RM-001")
    trx.tambah_layanan(KonsultasiDokter("K-1", "Konsultasi Spesialis", 75000, 45000))
    trx.tambah_layanan(TindakanMedis("T-1", "Jahit Luka", 50000, 20000))
    trx.tambah_layanan(PenjualanObat("O-1", "Amoxicillin", 8500, 2, 1500))

    # (75000+45000) + (50000+20000) + (8500*2 + 1500) = 120000 + 70000 + 18500 = 208500
    assert trx.hitung_grand_total() == 208500.0

    with pytest.raises(ValueError, match="kurang"):
        trx.proses_pembayaran(200000)

    kembalian = trx.proses_pembayaran(250000, "Tunai")
    assert kembalian == 41500.0
    assert trx.is_lunas() is True


def test_static_polymorphism_overloading():
    p1 = Pasien("RM-2026-0001", "3526011205920001", "Budi Santoso", date(1992, 5, 12))
    p2 = Pasien("RM-2026-0002", "3526010907580005", "Joko Susilo", date(1958, 7, 9))

    # PasienRepository.cari_pasien overloading
    repo = PasienRepository(items=[p1, p2])
    assert repo.cari_pasien("RM-2026-0001") == p1
    hasil_alt = repo.cari_pasien("Joko", date(1958, 7, 9))
    assert len(hasil_alt) == 1 and hasil_alt[0] == p2

    # AntreanManager.tambah_antrean overloading (Reguler FIFO vs Prioritas Darurat/Lansia)
    manager = AntreanManager()
    a1 = manager.tambah_antrean(p1)
    a2 = manager.tambah_antrean(p2, TingkatUrgensi.DARURAT, JenisPoli.POLI_UMUM)

    assert a1.get_prioritas() == TingkatUrgensi.REGULER
    assert a2.get_prioritas() == TingkatUrgensi.DARURAT

    dipanggil = manager.panggil_berikutnya_memori(JenisPoli.POLI_UMUM)
    assert dipanggil is not None
    assert dipanggil.get_nomor_antrean() == a2.get_nomor_antrean()
    assert dipanggil.get_status() == StatusAntrean.DIPERIKSA


def test_rekam_medis_and_farmasi_workflow_domain():
    pwd_hash = hash_password_sha256("medika123")
    dokter = Dokter("D1", "dr. Indah", "dokter", pwd_hash, "SIP-01", "Umum", 50000)
    farmasi = PetugasFarmasi("F1", "Rizky", "farmasi", pwd_hash, "STRTTK-01")
    pasien = Pasien("RM-001", "3526011205920001", "Budi", date(1992, 5, 12))
    obat = Obat("OBT-001", "Paracetamol 500mg", 20, 3500)

    rm = dokter.periksa_pasien(
        pasien,
        id_rekam_medis="RMED-001",
        keluhan_utama="Demam 3 hari",
        diagnosis="R50.9 - Fever",
        tindakan=[TindakanMedis("T-1", "Pemeriksaan Fisik", 25000, 5000)],
    )
    dokter.buat_resep(rm, [(obat, 3, "3x1", 0.0)])
    assert isinstance(rm, RekamMedis)
    assert len(rm.get_daftar_resep()) == 1

    farmasi.validasi_resep(rm)
    assert obat.get_stok() == 17
    assert rm.get_status_resep() == "Divalidasi"
