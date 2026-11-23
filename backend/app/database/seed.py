from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password_sha256
from app.database.models import (
    AntreanModel,
    DetailLayananTransaksiModel,
    DetailResepModel,
    DetailTindakanModel,
    ObatModel,
    PasienModel,
    PenggunaModel,
    RekamMedisModel,
    TransaksiPembayaranModel,
)
from app.domain.enums import (
    JenisPoli,
    MetodePembayaran,
    PeranPengguna,
    StatusAntrean,
    StatusResep,
    TingkatUrgensi,
)


async def seed_database(session: AsyncSession) -> None:
    """Mengisi data awal MedikaCare jika database masih kosong."""
    existing_users = await session.execute(select(PenggunaModel).limit(1))
    if existing_users.scalar_one_or_none() is not None:
        return

    default_pwd_hash = hash_password_sha256("medika123")

    users = [
        PenggunaModel(
            id_pengguna="USR-ADM-01",
            nama_lengkap="Nadia Kusuma",
            username="admin",
            password_hash=default_pwd_hash,
            peran=PeranPengguna.PETUGAS_ADMINISTRASI,
            kode_staf="ADM-001",
            shift_kerja="Pagi (07.00 - 14.00)",
        ),
        PenggunaModel(
            id_pengguna="USR-DOK-01",
            nama_lengkap="dr. Indah Permatasari",
            username="dokter",
            password_hash=default_pwd_hash,
            peran=PeranPengguna.DOKTER,
            nomor_sip="503/SIP-DU/2024/0192",
            spesialisasi="Dokter Umum",
            tarif_konsultasi=50000.0,
            tunjangan_spesialis=0.0,
            poli_praktik=JenisPoli.POLI_UMUM,
            shift_kerja="Pagi (08.00 - 14.00)",
        ),
        PenggunaModel(
            id_pengguna="USR-DOK-02",
            nama_lengkap="drg. Hendra Wijaya",
            username="dokter_gigi",
            password_hash=default_pwd_hash,
            peran=PeranPengguna.DOKTER,
            nomor_sip="503/SIP-DG/2024/0088",
            spesialisasi="Dokter Gigi",
            tarif_konsultasi=65000.0,
            tunjangan_spesialis=25000.0,
            poli_praktik=JenisPoli.POLI_GIGI,
            shift_kerja="Pagi (08.00 - 14.00)",
        ),
        PenggunaModel(
            id_pengguna="USR-DOK-03",
            nama_lengkap="dr. Ratna Dewi, Sp.A",
            username="dokter_anak",
            password_hash=default_pwd_hash,
            peran=PeranPengguna.DOKTER,
            nomor_sip="503/SIP-SPA/2024/0311",
            spesialisasi="Spesialis Anak",
            tarif_konsultasi=75000.0,
            tunjangan_spesialis=45000.0,
            poli_praktik=JenisPoli.POLI_ANAK,
            shift_kerja="Siang (10.00 - 16.00)",
        ),
        PenggunaModel(
            id_pengguna="USR-FRM-01",
            nama_lengkap="Rizky Pratama, S.Farm., Apt",
            username="farmasi",
            password_hash=default_pwd_hash,
            peran=PeranPengguna.PETUGAS_FARMASI,
            nomor_strttk="STRTTK-19950412/2023/1104",
            shift_kerja="Pagi (08.00 - 15.00)",
        ),
        PenggunaModel(
            id_pengguna="USR-KSR-01",
            nama_lengkap="Sinta Rahayu",
            username="kasir",
            password_hash=default_pwd_hash,
            peran=PeranPengguna.KASIR,
            nomor_loket="Loket 01",
            shift_kerja="Pagi (08.00 - 15.00)",
        ),
    ]
    session.add_all(users)

    obats = [
        ObatModel(
            kode_obat="OBT-001",
            nama_obat="Paracetamol 500mg",
            stok=150,
            harga_satuan=3500.0,
            satuan="Strip",
            kategori="Analgesik & Antipiretik",
        ),
        ObatModel(
            kode_obat="OBT-002",
            nama_obat="Amoxicillin 500mg",
            stok=90,
            harga_satuan=8500.0,
            satuan="Strip",
            kategori="Antibiotik",
        ),
        ObatModel(
            kode_obat="OBT-003",
            nama_obat="Antasida Doen Sirup 60ml",
            stok=45,
            harga_satuan=14000.0,
            satuan="Botol",
            kategori="Saluran Cerna",
        ),
        ObatModel(
            kode_obat="OBT-004",
            nama_obat="Cetirizine 10mg",
            stok=120,
            harga_satuan=5500.0,
            satuan="Strip",
            kategori="Antihistamin",
        ),
        ObatModel(
            kode_obat="OBT-005",
            nama_obat="Vitamin B Complex",
            stok=200,
            harga_satuan=4500.0,
            satuan="Strip",
            kategori="Suplemen",
        ),
        ObatModel(
            kode_obat="OBT-006",
            nama_obat="Ibuprofen 400mg",
            stok=85,
            harga_satuan=6000.0,
            satuan="Strip",
            kategori="Antiinflamasi",
        ),
        ObatModel(
            kode_obat="OBT-007",
            nama_obat="Oralit 200ml Sachet",
            stok=110,
            harga_satuan=2500.0,
            satuan="Sachet",
            kategori="Elektrolit",
        ),
        ObatModel(
            kode_obat="OBT-008",
            nama_obat="Salbutamol 2mg",
            stok=14,
            harga_satuan=7000.0,
            satuan="Strip",
            kategori="Pernapasan",
        ),
    ]
    session.add_all(obats)

    pasiens = [
        PasienModel(
            nomor_rm="RM-2026-0001",
            nik="3526011205920001",
            nama="Budi Santoso",
            tanggal_lahir=date(1992, 5, 12),
            jenis_kelamin="Laki-laki",
            alamat="Jl. Trunojoyo No. 14, Bangkalan",
            no_telepon="081234567801",
            riwayat_alergi="Tidak ada",
            aktif=True,
        ),
        PasienModel(
            nomor_rm="RM-2026-0002",
            nik="3526014508950002",
            nama="Siti Aminah",
            tanggal_lahir=date(1995, 8, 5),
            jenis_kelamin="Perempuan",
            alamat="Jl. Jokotole No. 88, Bangkalan",
            no_telepon="081234567802",
            riwayat_alergi="Alergi Penisilin",
            aktif=True,
        ),
        PasienModel(
            nomor_rm="RM-2026-0003",
            nik="3526011803880003",
            nama="Agus Setiawan",
            tanggal_lahir=date(1988, 3, 18),
            jenis_kelamin="Laki-laki",
            alamat="Perum Telang Indah Blok C-7, Kamal",
            no_telepon="081234567803",
            riwayat_alergi="Tidak ada",
            aktif=True,
        ),
        PasienModel(
            nomor_rm="RM-2026-0004",
            nik="3526016211990004",
            nama="Rina Marlina",
            tanggal_lahir=date(1999, 11, 22),
            jenis_kelamin="Perempuan",
            alamat="Jl. Raya Telang No. 45, Kamal",
            no_telepon="081234567804",
            riwayat_alergi="Seafood & Udang",
            aktif=True,
        ),
        PasienModel(
            nomor_rm="RM-2026-0005",
            nik="3526010907580005",
            nama="Joko Susilo",
            tanggal_lahir=date(1958, 7, 9),
            jenis_kelamin="Laki-laki",
            alamat="Jl. Panglima Sudirman No. 23, Bangkalan",
            no_telepon="081234567805",
            riwayat_alergi="Aspirin",
            aktif=True,
        ),
        PasienModel(
            nomor_rm="RM-2026-0006",
            nik="3526015004210006",
            nama="Alya Zahra",
            tanggal_lahir=date(2021, 4, 10),
            jenis_kelamin="Perempuan",
            alamat="Jl. Soekarno Hatta No. 9, Bangkalan",
            no_telepon="081234567806",
            riwayat_alergi="Tidak ada",
            aktif=True,
        ),
    ]
    session.add_all(pasiens)
    await session.flush()

    now = datetime.now()

    # 1 kunjungan sudah selesai & lunas hari ini (untuk riwayat & statistik pendapatan awal)
    ant_selesai = AntreanModel(
        nomor_antrean="A-001",
        pasien_nomor_rm="RM-2026-0003",
        poli_tujuan=JenisPoli.POLI_UMUM,
        prioritas=TingkatUrgensi.REGULER,
        status=StatusAntrean.SELESAI,
        waktu_daftar=now - timedelta(hours=2),
        waktu_panggil=now - timedelta(hours=1, minutes=45),
    )
    # 1 pasien sudah diperiksa, resep menunggu validasi farmasi & pembayaran kasir
    ant_diperiksa_selesai = AntreanModel(
        nomor_antrean="A-002",
        pasien_nomor_rm="RM-2026-0001",
        poli_tujuan=JenisPoli.POLI_UMUM,
        prioritas=TingkatUrgensi.REGULER,
        status=StatusAntrean.SELESAI_DIPERIKSA,
        waktu_daftar=now - timedelta(hours=1, minutes=20),
        waktu_panggil=now - timedelta(hours=1, minutes=5),
    )
    # Antrean menunggu aktif
    ant_m1 = AntreanModel(
        nomor_antrean="A-003",
        pasien_nomor_rm="RM-2026-0002",
        poli_tujuan=JenisPoli.POLI_UMUM,
        prioritas=TingkatUrgensi.REGULER,
        status=StatusAntrean.MENUNGGU,
        waktu_daftar=now - timedelta(minutes=35),
    )
    ant_m2 = AntreanModel(
        nomor_antrean="A-004",
        pasien_nomor_rm="RM-2026-0005",
        poli_tujuan=JenisPoli.POLI_UMUM,
        prioritas=TingkatUrgensi.LANSIA,
        status=StatusAntrean.MENUNGGU,
        waktu_daftar=now - timedelta(minutes=25),
    )
    ant_g1 = AntreanModel(
        nomor_antrean="G-001",
        pasien_nomor_rm="RM-2026-0004",
        poli_tujuan=JenisPoli.POLI_GIGI,
        prioritas=TingkatUrgensi.REGULER,
        status=StatusAntrean.MENUNGGU,
        waktu_daftar=now - timedelta(minutes=18),
    )
    ant_k1 = AntreanModel(
        nomor_antrean="K-001",
        pasien_nomor_rm="RM-2026-0006",
        poli_tujuan=JenisPoli.POLI_ANAK,
        prioritas=TingkatUrgensi.PRIORITAS if hasattr(TingkatUrgensi, "PRIORITAS") else TingkatUrgensi.REGULER,
        status=StatusAntrean.MENUNGGU,
        waktu_daftar=now - timedelta(minutes=12),
    )
    session.add_all([ant_selesai, ant_diperiksa_selesai, ant_m1, ant_m2, ant_g1, ant_k1])
    await session.flush()

    # Rekam medis 1 (lunas)
    rm1 = RekamMedisModel(
        id_rekam_medis="RMED-20261123-001",
        pasien_nomor_rm="RM-2026-0003",
        dokter_id="USR-DOK-01",
        antrean_id=ant_selesai.id,
        tanggal_periksa=date.today(),
        keluhan_utama="Nyeri kepala dan tenggorokan kering sejak 2 hari",
        tekanan_darah="120/80 mmHg",
        suhu_tubuh=37.2,
        denyut_nadi=82,
        diagnosis="J02.9 - Faringitis Akut",
        catatan_dokter="Istirahat cukup dan perbanyak air mineral.",
        status_resep=StatusResep.DIVALIDASI,
        created_at=now - timedelta(hours=1, minutes=30),
    )
    rm1.tindakan_list.append(
        DetailTindakanModel(
            kode_layanan="TND-01",
            nama_layanan="Pemeriksaan Fisik & THT Dasar",
            tarif_dasar=25000.0,
            biaya_alat_habis_pakai=5000.0,
        )
    )
    rm1.resep_list.append(
        DetailResepModel(
            kode_obat="OBT-001",
            nama_obat="Paracetamol 500mg",
            jumlah_beli=1,
            dosis="3x1 tab sesudah makan",
            harga_satuan=3500.0,
            biaya_racik=0.0,
            tervalidasi=True,
        )
    )
    rm1.resep_list.append(
        DetailResepModel(
            kode_obat="OBT-005",
            nama_obat="Vitamin B Complex",
            jumlah_beli=1,
            dosis="1x1 tab pagi hari",
            harga_satuan=4500.0,
            biaya_racik=0.0,
            tervalidasi=True,
        )
    )

    # Rekam medis 2 (siap divalidasi farmasi & dibayar di kasir)
    rm2 = RekamMedisModel(
        id_rekam_medis="RMED-20261123-002",
        pasien_nomor_rm="RM-2026-0001",
        dokter_id="USR-DOK-01",
        antrean_id=ant_diperiksa_selesai.id,
        tanggal_periksa=date.today(),
        keluhan_utama="Demam tinggi sejak 3 hari, pusing dan mual",
        tekanan_darah="120/80 mmHg",
        suhu_tubuh=38.5,
        denyut_nadi=88,
        diagnosis="A09 - Gastroenteritis Akut & Febris",
        catatan_dokter="Observasi hidrasi, kontrol ulang jika demam tidak turun dalam 48 jam.",
        status_resep=StatusResep.MENUNGGU_VALIDASI,
        created_at=now - timedelta(minutes=55),
    )
    rm2.tindakan_list.append(
        DetailTindakanModel(
            kode_layanan="TND-02",
            nama_layanan="Pemeriksaan Fisik Abdomen & Injeksi Vitamin",
            tarif_dasar=35000.0,
            biaya_alat_habis_pakai=15000.0,
        )
    )
    rm2.resep_list.append(
        DetailResepModel(
            kode_obat="OBT-001",
            nama_obat="Paracetamol 500mg",
            jumlah_beli=2,
            dosis="3x1 tab bila demam",
            harga_satuan=3500.0,
            biaya_racik=0.0,
            tervalidasi=False,
        )
    )
    rm2.resep_list.append(
        DetailResepModel(
            kode_obat="OBT-003",
            nama_obat="Antasida Doen Sirup 60ml",
            jumlah_beli=1,
            dosis="3x1 sendok takar sebelum makan",
            harga_satuan=14000.0,
            biaya_racik=2000.0,
            tervalidasi=False,
        )
    )
    session.add_all([rm1, rm2])
    await session.flush()

    # Transaksi lunas untuk rm1
    trx1 = TransaksiPembayaranModel(
        id_transaksi="TRX-20261123-001",
        pasien_nomor_rm="RM-2026-0003",
        rekam_medis_id=rm1.id_rekam_medis,
        kasir_id="USR-KSR-01",
        waktu=now - timedelta(hours=1, minutes=15),
        grand_total=88000.0,
        nominal_bayar=100000.0,
        kembalian=12000.0,
        metode_pembayaran=MetodePembayaran.TUNAI,
        status_lunas=True,
    )
    trx1.layanan_list.extend(
        [
            DetailLayananTransaksiModel(
                tipe_layanan="KonsultasiDokter",
                kode_layanan="KONS-UMUM",
                nama_layanan="Konsultasi dr. Indah Permatasari (Dokter Umum)",
                tarif_dasar=50000.0,
                biaya_tambahan=0.0,
                jumlah=1,
                subtotal=50000.0,
            ),
            DetailLayananTransaksiModel(
                tipe_layanan="TindakanMedis",
                kode_layanan="TND-01",
                nama_layanan="Pemeriksaan Fisik & THT Dasar",
                tarif_dasar=25000.0,
                biaya_tambahan=5000.0,
                jumlah=1,
                subtotal=30000.0,
            ),
            DetailLayananTransaksiModel(
                tipe_layanan="PenjualanObat",
                kode_layanan="OBT-001",
                nama_layanan="Paracetamol 500mg",
                tarif_dasar=3500.0,
                biaya_tambahan=0.0,
                jumlah=1,
                subtotal=3500.0,
            ),
            DetailLayananTransaksiModel(
                tipe_layanan="PenjualanObat",
                kode_layanan="OBT-005",
                nama_layanan="Vitamin B Complex",
                tarif_dasar=4500.0,
                biaya_tambahan=0.0,
                jumlah=1,
                subtotal=4500.0,
            ),
        ]
    )

    # Transaksi belum lunas (menunggu pembayaran) untuk rm2
    trx2 = TransaksiPembayaranModel(
        id_transaksi="TRX-20261123-002",
        pasien_nomor_rm="RM-2026-0001",
        rekam_medis_id=rm2.id_rekam_medis,
        kasir_id=None,
        waktu=now - timedelta(minutes=50),
        grand_total=123000.0,
        nominal_bayar=0.0,
        kembalian=0.0,
        metode_pembayaran=MetodePembayaran.TUNAI,
        status_lunas=False,
    )
    trx2.layanan_list.extend(
        [
            DetailLayananTransaksiModel(
                tipe_layanan="KonsultasiDokter",
                kode_layanan="KONS-UMUM",
                nama_layanan="Konsultasi dr. Indah Permatasari (Dokter Umum)",
                tarif_dasar=50000.0,
                biaya_tambahan=0.0,
                jumlah=1,
                subtotal=50000.0,
            ),
            DetailLayananTransaksiModel(
                tipe_layanan="TindakanMedis",
                kode_layanan="TND-02",
                nama_layanan="Pemeriksaan Fisik Abdomen & Injeksi Vitamin",
                tarif_dasar=35000.0,
                biaya_tambahan=15000.0,
                jumlah=1,
                subtotal=50000.0,
            ),
            DetailLayananTransaksiModel(
                tipe_layanan="PenjualanObat",
                kode_layanan="OBT-001",
                nama_layanan="Paracetamol 500mg",
                tarif_dasar=3500.0,
                biaya_tambahan=0.0,
                jumlah=2,
                subtotal=7000.0,
            ),
            DetailLayananTransaksiModel(
                tipe_layanan="PenjualanObat",
                kode_layanan="OBT-003",
                nama_layanan="Antasida Doen Sirup 60ml",
                tarif_dasar=14000.0,
                biaya_tambahan=2000.0,
                jumlah=1,
                subtotal=16000.0,
            ),
        ]
    )
    session.add_all([trx1, trx2])
    await session.commit()
