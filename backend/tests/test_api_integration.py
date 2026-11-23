from __future__ import annotations

import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.seed import seed_database
from app.database.session import Base, get_db_session
from app.main import app


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    db_file = tmp_path / "test_medikacare.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_file.as_posix()}", echo=False)
    TestSessionLocal = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        await seed_database(session)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def login_as(client: AsyncClient, username: str, peran: str) -> str:
    res = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "medika123", "peran": peran},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_auth_and_rbac_enforcement(client: AsyncClient):
    # Salah password
    bad = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )
    assert bad.status_code == 401

    # Kasir tidak boleh mendaftarkan pasien (RBAC 403)
    kasir_token = await login_as(client, "kasir", "Kasir")
    forbidden = await client.post(
        "/api/pasien",
        headers={"Authorization": f"Bearer {kasir_token}"},
        json={
            "nik": "3526011205929999",
            "nama": "Pasien Uji",
            "tanggal_lahir": "1995-01-01",
            "jenis_kelamin": "Laki-laki",
        },
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_full_end_to_end_clinical_flow(client: AsyncClient):
    admin_token = await login_as(client, "admin", "PetugasAdministrasi")
    dokter_token = await login_as(client, "dokter", "Dokter")
    farmasi_token = await login_as(client, "farmasi", "PetugasFarmasi")
    kasir_token = await login_as(client, "kasir", "Kasir")

    # 1. Validasi NIK salah (<16 digit) ditolak
    bad_nik = await client.post(
        "/api/pasien",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nik": "12345",
            "nama": "Dewi Lestari",
            "tanggal_lahir": "1996-04-15",
            "jenis_kelamin": "Perempuan",
        },
    )
    assert bad_nik.status_code in (400, 422)

    # 2. Resepsionis daftarkan pasien baru
    res_p = await client.post(
        "/api/pasien",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nik": "3526015504960099",
            "nama": "Dewi Lestari",
            "tanggal_lahir": "1996-04-15",
            "jenis_kelamin": "Perempuan",
            "alamat": "Jl. Raya Kamal No. 10",
            "no_telepon": "081299998888",
            "riwayat_alergi": "Sulfa",
        },
    )
    assert res_p.status_code == 201, res_p.text
    pasien = res_p.json()
    assert pasien["nomor_rm"].startswith("RM-")

    # 3. Resepsionis terbitkan antrean Darurat di Poli Umum agar dipanggil pertama
    res_a = await client.post(
        "/api/antrean",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "pasien_nomor_rm": pasien["nomor_rm"],
            "poli_tujuan": "Poli Umum",
            "prioritas": "Darurat",
        },
    )
    assert res_a.status_code == 201, res_a.text
    antrean = res_a.json()
    assert antrean["status"] == "Menunggu"

    # 4. Dokter memanggil antrean berikutnya (harus memanggil pasien Darurat)
    res_call = await client.post(
        "/api/antrean/panggil?poli=Poli%20Umum",
        headers={"Authorization": f"Bearer {dokter_token}"},
    )
    assert res_call.status_code == 200, res_call.text
    called = res_call.json()
    assert called["id"] == antrean["id"]
    assert called["status"] == "Diperiksa"

    # 5. Dokter simpan rekam medis + tindakan + resep obat digital
    res_rm = await client.post(
        "/api/rekam-medis",
        headers={"Authorization": f"Bearer {dokter_token}"},
        json={
            "pasien_nomor_rm": pasien["nomor_rm"],
            "antrean_id": called["id"],
            "keluhan_utama": "Sesak napas dan demam",
            "tekanan_darah": "110/70 mmHg",
            "suhu_tubuh": 38.2,
            "denyut_nadi": 94,
            "diagnosis": "J06.9 - ISPA Akut",
            "tindakan": [
                {
                    "kode_layanan": "TND-04",
                    "nama_layanan": "Nebulizer Terapi Pernapasan",
                    "tarif_dasar": 45000,
                    "biaya_alat_habis_pakai": 25000,
                }
            ],
            "resep": [
                {
                    "kode_obat": "OBT-001",
                    "jumlah_beli": 2,
                    "dosis": "3x1 sesudah makan",
                    "biaya_racik": 1000,
                }
            ],
        },
    )
    assert res_rm.status_code == 201, res_rm.text
    rm = res_rm.json()
    assert rm["status_resep"] == "Menunggu Validasi"

    # 6. Farmasi validasi resep & pastikan stok OBT-001 berkurang 2 (dari 150 -> 148)
    res_val = await client.post(
        f"/api/farmasi/resep/{rm['id_rekam_medis']}/validasi",
        headers={"Authorization": f"Bearer {farmasi_token}"},
    )
    assert res_val.status_code == 200, res_val.text
    assert res_val.json()["status_resep"] == "Divalidasi"

    obat_res = await client.get(
        "/api/obat?q=OBT-001",
        headers={"Authorization": f"Bearer {farmasi_token}"},
    )
    assert obat_res.json()[0]["stok"] == 148

    # 7. Kasir cek tagihan polimorfik:
    # KonsultasiDokter (50000) + TindakanMedis (45000+25000=70000) + PenjualanObat (3500*2+1000=8000) = 128000
    tagihan_res = await client.get(
        "/api/kasir/tagihan?status_lunas=false",
        headers={"Authorization": f"Bearer {kasir_token}"},
    )
    assert tagihan_res.status_code == 200
    target_bill = next(
        b for b in tagihan_res.json() if b["rekam_medis_id"] == rm["id_rekam_medis"]
    )
    assert target_bill["grand_total"] == 128000.0

    # Nominal kurang ditolak
    bad_pay = await client.post(
        f"/api/kasir/tagihan/{target_bill['id_transaksi']}/bayar",
        headers={"Authorization": f"Bearer {kasir_token}"},
        json={"nominal_bayar": 100000, "metode_pembayaran": "Tunai"},
    )
    assert bad_pay.status_code == 400

    # Pembayaran sah Rp150.000 -> kembalian Rp22.000
    ok_pay = await client.post(
        f"/api/kasir/tagihan/{target_bill['id_transaksi']}/bayar",
        headers={"Authorization": f"Bearer {kasir_token}"},
        json={"nominal_bayar": 150000, "metode_pembayaran": "Tunai"},
    )
    assert ok_pay.status_code == 200, ok_pay.text
    struk = ok_pay.json()
    assert struk["status_lunas"] is True
    assert struk["kembalian"] == 22000.0

    # 8. Laporan ringkasan operasional
    lap = await client.get(
        "/api/laporan/ringkasan",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert lap.status_code == 200
    assert lap.json()["total_pendapatan_hari_ini"] >= 128000.0


@pytest.mark.asyncio
async def test_public_patient_portal_self_service_queue(client: AsyncClient):
    # 1. Monitor publik tidak membutuhkan token dan menyamarkan nama pasien
    mon = await client.get("/api/public/antrean/monitor")
    assert mon.status_code == 200
    mon_data = mon.json()
    assert len(mon_data["poli"]) == 3

    # 2. Verifikasi pasien lama salah tanggal lahir ditolak (404)
    wrong_dob = await client.post(
        "/api/public/antrean/pasien-lama",
        json={
            "identitas": "RM-2026-0002",
            "tanggal_lahir": "1990-01-01",
            "poli_tujuan": "Poli Umum",
        },
    )
    assert wrong_dob.status_code == 404

    # 3. Pasien lama yang sudah punya antrean aktif hari ini (RM-2026-0002 = Siti Aminah)
    #    mendapatkan kembali tiket aktifnya tanpa duplikasi antrean
    existing_res = await client.post(
        "/api/public/antrean/pasien-lama",
        json={
            "identitas": "RM-2026-0002",
            "tanggal_lahir": "1995-08-05",
            "poli_tujuan": "Poli Umum",
        },
    )
    assert existing_res.status_code == 201
    existing_data = existing_res.json()
    assert existing_data["sudah_terdaftar_hari_ini"] is True
    assert existing_data["nomor_antrean"] == "A-003"

    # 4. Pasien baru lansia (lahir 1955-03-10 -> usia >= 60) otomatis mendapat prioritas Lansia
    new_res = await client.post(
        "/api/public/antrean/pasien-baru",
        json={
            "nik": "3526011003550077",
            "nama": "Hendra Kusuma",
            "tanggal_lahir": "1955-03-10",
            "jenis_kelamin": "Laki-laki",
            "alamat": "Jl. Merdeka No. 12",
            "no_telepon": "081233445566",
            "riwayat_alergi": "Tidak ada",
            "poli_tujuan": "Poli Gigi",
        },
    )
    assert new_res.status_code == 201, new_res.text
    new_data = new_res.json()
    assert new_data["sudah_terdaftar_hari_ini"] is False
    assert new_data["prioritas"] == "Lansia"
    assert new_data["poli_tujuan"] == "Poli Gigi"
    assert new_data["pasien_nomor_rm"].startswith("RM-")

    # 5. Cek status antrean publik dengan NIK & tanggal lahir
    cek = await client.get(
        "/api/public/antrean/cek",
        params={"identitas": "3526011003550077", "tanggal_lahir": "1955-03-10"},
    )
    assert cek.status_code == 200
    assert cek.json()["nomor_antrean"] == new_data["nomor_antrean"]

