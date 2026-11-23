const { test, expect } = require('@playwright/test');

const PAUSE_SCALE = Number(process.env.PAUSE_SCALE ?? 1);

async function jeda(page, ms = 1500) {
  if (PAUSE_SCALE <= 0) return;
  await page.waitForTimeout(Math.round(ms * PAUSE_SCALE));
}

async function tampilkanBanner(page, tahap, deskripsi) {
  await page.evaluate(
    ({ title, subtitle }) => {
      let el = document.getElementById('e2e-presenter-banner');
      if (!el) {
        el = document.createElement('div');
        el.id = 'e2e-presenter-banner';
        Object.assign(el.style, {
          position: 'fixed',
          bottom: '18px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: '99999',
          background: 'rgba(15, 23, 42, 0.92)',
          color: '#f8fafc',
          padding: '10px 20px',
          borderRadius: '999px',
          border: '1px solid rgba(56, 189, 248, 0.5)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          pointerEvents: 'none',
          maxWidth: '90vw',
        });
        document.body.appendChild(el);
      }
      el.innerHTML = `<span style="background:#2563eb;color:#fff;padding:3px 10px;border-radius:999px;font-weight:700;font-size:11.5px;white-space:nowrap;">${title}</span><span style="color:#e2e8f0;font-weight:500;">${subtitle}</span>`;
    },
    { title: tahap, subtitle: deskripsi }
  );
}

function generateUniquePatient() {
  const stamp = String(Date.now()).slice(-10);
  const nik = `352601${stamp}`;
  const nama = `Hendra Wijaya ${stamp.slice(-4)}`;
  return {
    nik,
    nama,
    // Lahir tahun 1958 agar otomatis mendapat prioritas Lansia dan dipanggil lebih dulu di Poli Gigi
    tanggalLahir: '1958-04-12',
    jenisKelamin: 'Laki-laki',
    poliTujuan: 'Poli Gigi',
    noTelepon: '081234567890',
    alergi: 'Penisilin',
    alamat: 'Jl. Trunojoyo No. 27, Bangkalan',
  };
}

test.describe('MedikaCare — End-to-End Alur Layanan Klinik', () => {
  test('Simulasi Presentasi Visual Lengkap: Pendaftaran Pasien hingga Cetak Struk Kasir', async ({
    page,
  }) => {
    const pasien = generateUniquePatient();

    // =========================================================================
    // BABAK 1: PORTAL PASIEN MANDIRI (TANPA AKUN)
    // =========================================================================
    await page.goto('/');
    await tampilkanBanner(
      page,
      'BABAK 1 / 6',
      'Halaman Login & Akses Portal Antrean Mandiri Pasien'
    );
    await expect(page.getByText('MEDIKACARE', { exact: true })).toBeVisible();
    await jeda(page, 1800);

    await page
      .getByRole('button', { name: /Pasien\? Ambil Nomor Antrean Mandiri/i })
      .click();
    await expect(
      page.getByText('MEDIKACARE — ANJUNGAN ANTREAN PASIEN')
    ).toBeVisible();
    await tampilkanBanner(
      page,
      'BABAK 1 / 6',
      'Papan Monitor Ruang Tunggu Real-Time (3 Poli) & Registrasi Pasien Baru'
    );
    await jeda(page, 2000);

    // Pindah ke Tab Pasien Baru
    await page.getByRole('button', { name: 'Pasien Baru' }).click();
    await jeda(page, 1000);

    const newPatientForm = page.locator('form');
    await newPatientForm.getByPlaceholder('3526xxxxxxxxxxxx').fill(pasien.nik);
    await newPatientForm.getByPlaceholder('Nama sesuai KTP / KK').fill(pasien.nama);
    await newPatientForm.locator('input[type="date"]').fill(pasien.tanggalLahir);
    await newPatientForm.locator('select').nth(0).selectOption(pasien.jenisKelamin);
    await newPatientForm.locator('select').nth(1).selectOption(pasien.poliTujuan);
    await newPatientForm.getByPlaceholder('0812xxxxxxxx').fill(pasien.noTelepon);
    await newPatientForm
      .getByPlaceholder('Tidak ada / Penisilin / dll')
      .fill(pasien.alergi);
    await newPatientForm
      .getByPlaceholder('Alamat tempat tinggal')
      .fill(pasien.alamat);

    await tampilkanBanner(
      page,
      'BABAK 1 / 6',
      `Mengisi Identitas ${pasien.nama} (NIK 16 digit, Alergi: ${pasien.alergi})`
    );
    await jeda(page, 1800);

    await page
      .getByRole('button', { name: 'Daftar Pasien Baru & Ambil Antrean' })
      .click();

    // Verifikasi Tiket Antrean Digital terbit dengan prioritas Lansia otomatis
    const ticketCard = page.locator('.card').filter({ hasText: 'Tiket Antrean Digital Anda' });
    await expect(ticketCard.getByText(pasien.nama)).toBeVisible();
    await expect(ticketCard.getByText('Lansia')).toBeVisible();

    const nomorAntrean = (
      await ticketCard.locator('.mono').first().innerText()
    ).trim();
    const nomorRm = (
      await ticketCard
        .locator('div')
        .filter({ hasText: /^Nomor Rekam Medis:/ })
        .locator('.mono')
        .innerText()
    ).trim();

    await tampilkanBanner(
      page,
      'BABAK 1 / 6',
      `Tiket ${nomorAntrean} (${nomorRm}) Terbit Otomatis dengan Prioritas Lansia`
    );
    await jeda(page, 2200);

    // Tampilkan Modal Cetak Tiket
    await page.getByRole('button', { name: 'Cetak / Simpan Tiket Antrean' }).click();
    await expect(page.getByText('Tiket Antrean Resmi')).toBeVisible();
    await jeda(page, 2000);
    await page.getByRole('button', { name: 'Tutup' }).click();
    await jeda(page, 800);

    // Kembali ke Login Staf Klinik
    await page.getByRole('button', { name: 'Login Staf Klinik' }).click();
    await jeda(page, 1000);

    // =========================================================================
    // BABAK 2: RESEPSIONIS / PETUGAS ADMINISTRASI VERIFIKASI DATA
    // =========================================================================
    await tampilkanBanner(
      page,
      'BABAK 2 / 6',
      'Login sebagai Petugas Administrasi (Resepsionis) — Role-Based Access'
    );
    await page.getByRole('button', { name: 'Resepsionis / Admin' }).click();
    await jeda(page, 1000);
    await page.getByRole('button', { name: 'Masuk ke Sistem MedikaCare' }).click();

    await expect(page.getByText('DASHBOARD OPERASIONAL MEDIKACARE')).toBeVisible();
    await jeda(page, 1500);

    // Buka menu Pendaftaran Pasien & cari pasien baru
    await page.locator('.sidebar').getByRole('button', { name: 'Pendaftaran Pasien' }).click();
    await page
      .getByPlaceholder('Cari NRM, NIK, atau Nama...')
      .fill(pasien.nama);
    await expect(page.getByRole('cell', { name: pasien.nama })).toBeVisible();
    await expect(page.getByText(pasien.alergi).first()).toBeVisible();
    await tampilkanBanner(
      page,
      'BABAK 2 / 6',
      `Data Pasien ${pasien.nama} (${nomorRm}) & Alergi Terverifikasi di Resepsionis`
    );
    await jeda(page, 2000);

    // Buka menu Antrean Poli
    await page.locator('.sidebar').getByRole('button', { name: /^Antrean Poli/ }).click();
    await expect(page.getByText(nomorAntrean).first()).toBeVisible();
    await jeda(page, 1500);

    await page.getByRole('button', { name: 'Keluar Akun' }).click();
    await jeda(page, 1000);

    // =========================================================================
    // BABAK 3: DOKTER PEMERIKSA — PANGGIL ANTREAN, REKAM MEDIS & RESEP DIGITAL
    // =========================================================================
    await tampilkanBanner(
      page,
      'BABAK 3 / 6',
      'Login sebagai Dokter Pemeriksa (drg. Hendra Wijaya — Poli Gigi)'
    );
    await page.getByRole('button', { name: 'Dokter Pemeriksa' }).click();
    await page.locator('#login-username').fill('dokter_gigi');
    await page.locator('#login-password').fill('medika123');
    await jeda(page, 1200);
    await page.getByRole('button', { name: 'Masuk ke Sistem MedikaCare' }).click();

    await expect(
      page.locator('.sidebar').getByText('drg. Hendra Wijaya', { exact: true })
    ).toBeVisible();
    await jeda(page, 1500);

    // Masuk Ruang Periksa Dokter
    await page.locator('.sidebar').getByRole('button', { name: 'Pemeriksaan Dokter' }).click();
    await tampilkanBanner(
      page,
      'BABAK 3 / 6',
      `Dokter Memanggil Antrean Prioritas ${nomorAntrean} (${pasien.nama})`
    );
    await jeda(page, 1400);

    await page
      .getByRole('button', { name: /PANGGIL ANTREAN BERIKUTNYA/i })
      .click();

    // Pastikan peringatan alergi tampil di ruang periksa dokter
    await expect(
      page.getByText(`PERINGATAN ALERGI: ${pasien.alergi}`)
    ).toBeVisible();
    await jeda(page, 2000);

    // Isi Anamnesis, Tanda Vital & Diagnosis ICD-10
    await tampilkanBanner(
      page,
      'BABAK 3 / 6',
      'Mengisi Anamnesis, Tanda Vital, Diagnosis ICD-10, Tindakan & Resep Digital'
    );
    await page
      .getByPlaceholder('Contoh: Demam tinggi sejak 3 hari, pusing dan mual...')
      .fill('Sakit gigi geraham kanan bawah berdenyut sejak 2 hari, nyeri saat mengunyah.');
    await page
      .getByPlaceholder('Contoh: A09 - Gastroenteritis Akut & Febris')
      .fill('K04.0 - Pulpitis Akut');
    await page
      .getByPlaceholder('Anjuran istirahat / kontrol ulang...')
      .fill('Hindari antibiotik golongan penisilin karena riwayat alergi.');
    await jeda(page, 1200);

    // Tambah Tindakan Medis: Scaling / Pembersihan Karang Gigi
    const tindakanSection = page
      .locator('div')
      .filter({ has: page.getByText('Tindakan Medis (Komponen LayananKlinik)') })
      .last();
    await page.locator('select').nth(1).selectOption('TND-05');
    await page.getByRole('button', { name: 'Tambah', exact: true }).click();
    await expect(page.getByText('Scaling / Pembersihan Karang Gigi').last()).toBeVisible();
    await jeda(page, 1200);

    // Tambah Resep Obat Digital: Ibuprofen 400mg (OBT-006)
    await page.locator('select').nth(2).selectOption('OBT-006');
    await page.getByPlaceholder('Qty').fill('2');
    await page.getByPlaceholder('Dosis pakai').fill('3x1 sesudah makan bila nyeri');
    await page.getByPlaceholder('Racik').fill('1000');
    await page.getByRole('button', { name: 'Tambah Resep Obat' }).click();
    await expect(page.getByText('Ibuprofen 400mg x2')).toBeVisible();
    await jeda(page, 1500);

    await page
      .getByRole('button', { name: 'Simpan & Rujuk Farmasi / Kasir' })
      .click();
    await expect(page.getByText(/tersimpan & dirujuk ke Farmasi\/Kasir/i)).toBeVisible();
    await jeda(page, 1800);

    await page.getByRole('button', { name: 'Keluar Akun' }).click();
    await jeda(page, 1000);

    // =========================================================================
    // BABAK 4: PETUGAS FARMASI — VALIDASI RESEP & POTONG STOK OBAT
    // =========================================================================
    await tampilkanBanner(
      page,
      'BABAK 4 / 6',
      'Login sebagai Petugas Farmasi untuk Validasi Resep Digital'
    );
    await page.getByRole('button', { name: 'Petugas Farmasi' }).click();
    await jeda(page, 1000);
    await page.getByRole('button', { name: 'Masuk ke Sistem MedikaCare' }).click();

    await page.locator('.sidebar').getByRole('button', { name: /^Farmasi & Obat/ }).click();
    const resepCard = page
      .locator('div')
      .filter({ hasText: pasien.nama })
      .filter({ has: page.getByRole('button', { name: 'Validasi & Siapkan Obat' }) })
      .last();
    await expect(resepCard).toBeVisible();
    await tampilkanBanner(
      page,
      'BABAK 4 / 6',
      `Memvalidasi Resep ${pasien.nama} & Memperbarui Stok Obat Otomatis`
    );
    await jeda(page, 1800);

    await resepCard
      .getByRole('button', { name: 'Validasi & Siapkan Obat' })
      .click();
    await expect(page.getByText(/divalidasi dan stok inventaris obat telah diperbarui/i)).toBeVisible();
    await jeda(page, 2000);

    await page.getByRole('button', { name: 'Keluar Akun' }).click();
    await jeda(page, 1000);

    // =========================================================================
    // BABAK 5: KASIR KLINIK — KALKULASI POLIMORFIK, PEMBAYARAN & CETAK STRUK
    // =========================================================================
    await tampilkanBanner(
      page,
      'BABAK 5 / 6',
      'Login sebagai Kasir Klinik untuk Verifikasi Tagihan Polimorfik'
    );
    await page.getByRole('button', { name: 'Kasir Klinik' }).click();
    await jeda(page, 1000);
    await page.getByRole('button', { name: 'Masuk ke Sistem MedikaCare' }).click();

    await page.locator('.sidebar').getByRole('button', { name: /^Kasir & Pembayaran/ }).click();
    const tagihanRow = page.locator('tbody tr').filter({ hasText: pasien.nama }).first();
    await expect(tagihanRow).toBeVisible();
    await tagihanRow.click();
    await jeda(page, 1500);

    // Verifikasi 3 komponen kelas turunan LayananKlinik muncul pada rincian tagihan
    await expect(page.getByText('KonsultasiDokter').first()).toBeVisible();
    await expect(page.getByText('TindakanMedis').first()).toBeVisible();
    await expect(page.getByText('PenjualanObat').first()).toBeVisible();
    await tampilkanBanner(
      page,
      'BABAK 5 / 6',
      'Rincian Polimorfik (KonsultasiDokter + TindakanMedis + PenjualanObat)'
    );
    await jeda(page, 2000);

    // Demo validasi nominal pembayaran kurang
    const nominalInput = page.locator('input[type="number"]');
    await nominalInput.fill('50000');
    await expect(page.getByText(/Nominal pembayaran kurang/i)).toBeVisible();
    await tampilkanBanner(
      page,
      'BABAK 5 / 6',
      'Validasi Pembayaran Kurang Terdeteksi Otomatis Sebelum Diproses'
    );
    await jeda(page, 1800);

    // Input nominal cukup (Rp 300.000) -> kembalian dihitung otomatis
    await nominalInput.fill('300000');
    await expect(page.getByText('Uang Kembalian Otomatis:')).toBeVisible();
    await tampilkanBanner(
      page,
      'BABAK 5 / 6',
      'Memproses Pembayaran Tunai Rp 300.000 & Mencetak Struk Faktur Resmi'
    );
    await jeda(page, 1600);

    await page
      .getByRole('button', { name: 'Proses Pembayaran & Cetak Faktur' })
      .click();

    // Verifikasi Modal Faktur Pembayaran Resmi
    const receiptModal = page.locator('.modal-content');
    await expect(receiptModal.getByText('Faktur Pembayaran Resmi')).toBeVisible();
    await expect(receiptModal.getByText(/LUNAS/)).toBeVisible();
    await jeda(page, 2800);

    await receiptModal.getByRole('button', { name: 'Tutup' }).click();
    await jeda(page, 1000);

    // =========================================================================
    // BABAK 6: LAPORAN KUNJUNGAN & TEMA ADAPTIF LIGHT/DARK MODE
    // =========================================================================
    await page.locator('.sidebar').getByRole('button', { name: 'Laporan Kunjungan' }).click();
    await expect(page.getByText('Filter Periode Laporan & Rekapitulasi')).toBeVisible();
    await tampilkanBanner(
      page,
      'BABAK 6 / 6',
      'Laporan Kunjungan & Pendapatan Terupdate Real-Time + Adaptive Dark Mode'
    );
    await jeda(page, 2000);

    // Toggle Dark Mode lalu kembali ke Light Mode
    await page.getByRole('button', { name: 'Dark' }).click();
    await jeda(page, 1800);
    await page.getByRole('button', { name: 'Light' }).click();
    await tampilkanBanner(
      page,
      'SELESAI',
      `Seluruh Alur Layanan Pasien ${pasien.nama} (${nomorAntrean}) Selesai dengan Sukses!`
    );
    await jeda(page, 2500);
  });
});
