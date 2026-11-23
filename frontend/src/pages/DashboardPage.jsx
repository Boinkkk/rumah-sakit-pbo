import React from 'react';
import {
  ArrowRight,
  BellRing,
  ClipboardList,
  CreditCard,
  Pill,
  Stethoscope,
  Users,
} from 'lucide-react';
import StatCards from '../components/StatCards';
import {
  formatJam,
  formatRupiah,
  prioritasBadge,
  statusAntreanBadge,
} from '../utils/formatters';

export default function DashboardPage({
  user,
  summary,
  antreanList,
  resepList,
  tagihanList,
  onNavigate,
  onPanggilBerikutnya,
  busyAction,
}) {
  const activeExam = antreanList.find((a) => a.status === 'Diperiksa');
  const pendingResep = resepList.filter((r) => r.status_resep === 'Menunggu Validasi');
  const pendingBills = tagihanList.filter((t) => !t.status_lunas);

  return (
    <div>
      <StatCards summary={summary} />

      <div className="grid-split">
        {/* Panel Kiri: Daftar Antrean Poli Live (Sesuai Rancangan Gambar 4.1) */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <ClipboardList size={17} color="var(--primary)" />
              Daftar Antrean Poli Hari Ini
            </h3>
            <span className="badge badge-primary">Real-Time Queue</span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>No</th>
                  <th>Nama Pasien</th>
                  <th>Poli</th>
                  <th>Prioritas</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {antreanList.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 24 }}>
                      Belum ada antrean terdaftar hari ini.
                    </td>
                  </tr>
                ) : (
                  antreanList.slice(0, 8).map((item) => (
                    <tr key={item.id}>
                      <td className="mono" style={{ fontWeight: 700 }}>
                        {item.nomor_antrean}
                      </td>
                      <td>
                        <div style={{ fontWeight: 600 }}>{item.pasien_nama}</div>
                        <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                          {item.pasien_nomor_rm} • {formatJam(item.waktu_daftar)}
                        </div>
                      </td>
                      <td>{item.poli_tujuan}</td>
                      <td>
                        <span className={`badge ${prioritasBadge(item.prioritas)}`}>
                          {item.prioritas}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${statusAntreanBadge(item.status)}`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="card-body" style={{ borderTop: '1px solid var(--border-color)', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {user.peran === 'Dokter' && (
              <button
                type="button"
                className="btn btn-primary"
                style={{ flex: 1 }}
                disabled={busyAction}
                onClick={() => onPanggilBerikutnya(user.poli_praktik || '')}
              >
                <BellRing size={16} />
                [PANGGIL ANTREAN BERIKUTNYA]
              </button>
            )}
            {user.peran === 'PetugasAdministrasi' && (
              <button
                type="button"
                className="btn btn-primary"
                style={{ flex: 1 }}
                onClick={() => onNavigate('antrean')}
              >
                Kelola Antrean & Pendaftaran
                <ArrowRight size={15} />
              </button>
            )}
            {user.peran === 'PetugasFarmasi' && (
              <button
                type="button"
                className="btn btn-primary"
                style={{ flex: 1 }}
                onClick={() => onNavigate('farmasi')}
              >
                Buka Antrean Resep Farmasi
                <ArrowRight size={15} />
              </button>
            )}
            {user.peran === 'Kasir' && (
              <button
                type="button"
                className="btn btn-primary"
                style={{ flex: 1 }}
                onClick={() => onNavigate('kasir')}
              >
                Buka Loket Pembayaran Kasir
                <ArrowRight size={15} />
              </button>
            )}
          </div>
        </div>

        {/* Panel Kanan: Ringkasan Operasional & Aksi Cepat Sesuai Peran */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <Stethoscope size={17} color="var(--teal)" />
                {activeExam
                  ? `Pemeriksaan Aktif: ${activeExam.pasien_nama} (${activeExam.nomor_antrean})`
                  : 'Status Alur Layanan Klinik'}
              </h3>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {activeExam ? (
                <div className="alert alert-info">
                  <div>
                    <div style={{ fontWeight: 700, marginBottom: 4 }}>
                      Pasien sedang berada di ruang periksa ({activeExam.poli_tujuan})
                    </div>
                    <div style={{ fontSize: 12.5 }}>
                      NRM: <span className="mono">{activeExam.pasien_nomor_rm}</span> • Alergi:{' '}
                      <strong>{activeExam.riwayat_alergi}</strong>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="alert alert-info">
                  <span>
                    Tidak ada pasien berstatus <strong>Diperiksa</strong> saat ini. Dokter dapat memanggil antrean berikutnya.
                  </span>
                </div>
              )}

              <div className="grid-2">
                <div
                  style={{
                    padding: 14,
                    borderRadius: 10,
                    background: 'var(--bg-surface-alt)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                    Resep Menunggu Validasi Farmasi
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--warning)' }}>
                    {pendingResep.length} Resep
                  </div>
                </div>
                <div
                  style={{
                    padding: 14,
                    borderRadius: 10,
                    background: 'var(--bg-surface-alt)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                    Tagihan Belum Lunas (Kasir)
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--primary)' }}>
                    {pendingBills.length} Tagihan
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                {user.peran === 'PetugasAdministrasi' && (
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => onNavigate('pasien')}
                  >
                    <Users size={15} />
                    Pendaftaran Pasien Baru
                  </button>
                )}
                {user.peran === 'Dokter' && (
                  <button
                    type="button"
                    className="btn btn-success"
                    onClick={() => onNavigate('pemeriksaan')}
                  >
                    <Stethoscope size={15} />
                    Buka Ruang Periksa Dokter
                  </button>
                )}
                {user.peran === 'PetugasFarmasi' && (
                  <button
                    type="button"
                    className="btn btn-warning"
                    onClick={() => onNavigate('farmasi')}
                  >
                    <Pill size={15} />
                    Validasi Resep Masuk ({pendingResep.length})
                  </button>
                )}
                {user.peran === 'Kasir' && (
                  <button
                    type="button"
                    className="btn btn-success"
                    onClick={() => onNavigate('kasir')}
                  >
                    <CreditCard size={15} />
                    Proses Tagihan ({pendingBills.length})
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Tagihan Terbaru</h3>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Kalkulasi Polimorfik LayananKlinik
              </span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID Transaksi</th>
                    <th>Pasien</th>
                    <th>Grand Total</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tagihanList.slice(0, 4).map((t) => (
                    <tr key={t.id_transaksi}>
                      <td className="mono" style={{ fontSize: 12.5 }}>{t.id_transaksi}</td>
                      <td>{t.pasien_nama}</td>
                      <td style={{ fontWeight: 700 }}>{formatRupiah(t.grand_total)}</td>
                      <td>
                        <span className={`badge ${t.status_lunas ? 'badge-success' : 'badge-warning'}`}>
                          {t.status_lunas ? 'Lunas' : 'Menunggu Bayar'}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {tagihanList.length === 0 && (
                    <tr>
                      <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                        Belum ada transaksi.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
