export function formatRupiah(amount) {
  const num = Number(amount || 0);
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatTanggalIndo(isoDateOrDatetime) {
  if (!isoDateOrDatetime) return '-';
  const d = new Date(isoDateOrDatetime);
  if (Number.isNaN(d.getTime())) return isoDateOrDatetime;
  return new Intl.DateTimeFormat('id-ID', {
    weekday: 'long',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(d);
}

export function formatWaktu(isoDatetime) {
  if (!isoDatetime) return '-';
  const d = new Date(isoDatetime);
  if (Number.isNaN(d.getTime())) return isoDatetime;
  return new Intl.DateTimeFormat('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
}

export function formatJam(isoDatetime) {
  if (!isoDatetime) return '-';
  const d = new Date(isoDatetime);
  if (Number.isNaN(d.getTime())) return '-';
  return new Intl.DateTimeFormat('id-ID', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
}

export const ROLE_LABELS = {
  PetugasAdministrasi: 'Petugas Administrasi',
  Dokter: 'Dokter Pemeriksa',
  PetugasFarmasi: 'Petugas Farmasi',
  Kasir: 'Kasir Klinik',
};

export function statusAntreanBadge(status) {
  switch (status) {
    case 'Diperiksa':
      return 'badge-teal';
    case 'Menunggu':
      return 'badge-warning';
    case 'Selesai Diperiksa':
      return 'badge-primary';
    case 'Selesai':
      return 'badge-success';
    default:
      return 'badge-muted';
  }
}

export function prioritasBadge(prioritas) {
  switch (prioritas) {
    case 'Darurat':
      return 'badge-danger';
    case 'Lansia':
      return 'badge-primary';
    default:
      return 'badge-muted';
  }
}
