# MedikaCare — Sistem Informasi Manajemen Layanan Klinik Kesehatan

Aplikasi berbasis web untuk manajemen operasional klinik pratama (**Klinik Pratama Sehat**) yang dibangun menggunakan **Python (FastAPI + SQLAlchemy Async + Pydantic v2 + SQLite)** dan **React (Vite)** dengan penerapan menyeluruh paradigma **Pemrograman Berorientasi Objek (PBO)**.

## Arsitektur & Penerapan PBO (`backend/app/domain/`)
1. **Encapsulation**:
   - `Pasien`: validasi ketat NIK 16 digit angka, tanggal lahir tidak di masa depan, perhitungan umur otomatis.
   - `Obat`: validasi stok dan harga satuan tidak boleh negatif (`kurangi_stok`, `tambah_stok`).
2. **Inheritance**:
   - Kelas abstrak `Pengguna (ABC)` menurunkan atribut identitas & autentikasi SHA-256 ke `Dokter`, `PetugasAdministrasi`, `PetugasFarmasi`, dan `Kasir`.
3. **Polymorphism**:
   - **Dynamic Polymorphism (Method Overriding)**: kelas abstrak `LayananKlinik` dioverride oleh `KonsultasiDokter`, `TindakanMedis`, dan `PenjualanObat` pada metode `hitung_total_biaya()`, diagregasi oleh `TransaksiPembayaran.hitung_grand_total()`.
   - **Static Polymorphism (Method Overloading)**: `@overload` & dispatch pada `AntreanManager.tambah_antrean(...)` dan `PasienRepository.cari_pasien(...)`.
4. **Association, Aggregation, Composition & Dependency**:
   - `Pasien *-- RekamMedis` (Composition), `TransaksiPembayaran *-- LayananKlinik` (Composition), `RekamMedis o-- Obat` & `AntreanManager o-- Antrean` (Aggregation), `BillingService ..> TransaksiPembayaran` (Dependency).

## Cara Menjalankan Aplikasi

### 1. Jalankan Backend (FastAPI + SQLite)
```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```
Dokumentasi API Swagger tersedia di: `http://127.0.0.1:8000/docs`

### 2. Jalankan Frontend (React + Vite)
```powershell
cd frontend
npm run dev
```
Buka aplikasi di browser: `http://localhost:5173`

### 3. Menjalankan Pengujian Otomatis (Pytest)
```powershell
cd backend
uv run pytest -v
```

### 4. Menjalankan E2E Testing Visual (Playwright)
Pastikan server backend (`8000`) dan frontend (`5173`) sedang berjalan, lalu jalankan dari folder `e2e`:
```powershell
cd e2e
# Mode presentasi visual (browser terbuka dengan slowMo + jeda antar tahap):
npm run test:demo

# Mode cepat (headless untuk regresi):
npm run test:fast
```
Anda juga dapat mengatur kecepatan presentasi lewat variabel lingkungan `SLOW_MO` (ms) dan `PAUSE_SCALE` (misal `PAUSE_SCALE=1.5` untuk jeda lebih lama saat presentasi).

## Akun Demo (Kata Sandi: `medika123`)
- **Petugas Administrasi (Resepsionis)**: username `admin`
- **Dokter Pemeriksa (Poli Umum)**: username `dokter` (juga tersedia `dokter_gigi`, `dokter_anak`)
- **Petugas Farmasi**: username `farmasi`
- **Kasir Klinik**: username `kasir`
