const API_BASE = '';

function getToken() {
  return localStorage.getItem('medikacare_token') || '';
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await res.json()
    : await res.text();

  if (!res.ok) {
    const msg =
      typeof data === 'object' && data !== null && data.detail
        ? Array.isArray(data.detail)
          ? data.detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
          : data.detail
        : 'Terjadi kesalahan saat menghubungi server.';
    const error = new Error(msg);
    error.status = res.status;
    throw error;
  }

  return data;
}

export const api = {
  // Auth
  login: (payload) =>
    request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getMe: () => request('/api/auth/me'),
  listDokter: () => request('/api/auth/dokter'),

  // Pasien
  listPasien: (q = '', includeInactive = false) =>
    request(
      `/api/pasien?q=${encodeURIComponent(q)}&include_inactive=${includeInactive}`
    ),
  createPasien: (payload) =>
    request('/api/pasien', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updatePasien: (nomorRm, payload) =>
    request(`/api/pasien/${encodeURIComponent(nomorRm)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deactivatePasien: (nomorRm) =>
    request(`/api/pasien/${encodeURIComponent(nomorRm)}/nonaktifkan`, {
      method: 'PATCH',
    }),

  // Antrean
  listAntrean: (poli = '') =>
    request(`/api/antrean${poli ? `?poli=${encodeURIComponent(poli)}` : ''}`),
  daftarAntrean: (payload) =>
    request('/api/antrean', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  panggilAntrean: (poli = '') =>
    request(
      `/api/antrean/panggil${poli ? `?poli=${encodeURIComponent(poli)}` : ''}`,
      { method: 'POST' }
    ),

  // Rekam Medis
  listRekamMedis: () => request('/api/rekam-medis'),
  listRekamMedisPasien: (nomorRm) =>
    request(`/api/rekam-medis/pasien/${encodeURIComponent(nomorRm)}`),
  createRekamMedis: (payload) =>
    request('/api/rekam-medis', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Farmasi & Obat
  listObat: (q = '') => request(`/api/obat?q=${encodeURIComponent(q)}`),
  createObat: (payload) =>
    request('/api/obat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateObat: (kodeObat, payload) =>
    request(`/api/obat/${encodeURIComponent(kodeObat)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  listResepFarmasi: (statusResep = '') =>
    request(
      `/api/farmasi/resep${
        statusResep ? `?status_resep=${encodeURIComponent(statusResep)}` : ''
      }`
    ),
  validasiResep: (idRekamMedis) =>
    request(`/api/farmasi/resep/${encodeURIComponent(idRekamMedis)}/validasi`, {
      method: 'POST',
    }),

  // Kasir
  listTagihan: (statusLunas = null) =>
    request(
      `/api/kasir/tagihan${
        statusLunas === null ? '' : `?status_lunas=${statusLunas}`
      }`
    ),
  bayarTagihan: (idTransaksi, payload) =>
    request(`/api/kasir/tagihan/${encodeURIComponent(idTransaksi)}/bayar`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Laporan
  getRingkasan: (mulai = '', akhir = '') => {
    const params = new URLSearchParams();
    if (mulai) params.set('tanggal_mulai', mulai);
    if (akhir) params.set('tanggal_akhir', akhir);
    const qs = params.toString();
    return request(`/api/laporan/ringkasan${qs ? `?${qs}` : ''}`);
  },

  // Portal Pasien Mandiri (Publik tanpa login staf)
  getPublicMonitor: () => request('/api/public/antrean/monitor'),
  ambilAntreanPasienLama: (payload) =>
    request('/api/public/antrean/pasien-lama', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  ambilAntreanPasienBaru: (payload) =>
    request('/api/public/antrean/pasien-baru', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  cekAntreanPasien: (identitas, tanggalLahir) =>
    request(
      `/api/public/antrean/cek?identitas=${encodeURIComponent(identitas)}&tanggal_lahir=${encodeURIComponent(tanggalLahir)}`
    ),
};
