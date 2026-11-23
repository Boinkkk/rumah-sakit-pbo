import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  Moon,
  Printer,
  Search,
  Sun,
  Ticket,
  UserPlus,
  Users,
} from 'lucide-react';
import { api } from '../services/api';
import { formatWaktu, prioritasBadge, statusAntreanBadge } from '../utils/formatters';

const EMPTY_NEW_PATIENT = {
  nik: '',
  nama: '',
  tanggal_lahir: '',
  jenis_kelamin: 'Laki-laki',
  no_telepon: '',
  alamat: '',
  riwayat_alergi: 'Tidak ada',
  poli_tujuan: 'Poli Umum',
};

export default function PatientPortalPage({
  onBackToLogin,
  onPrintTicket,
  onNotify,
  theme,
  onToggleTheme,
}) {
  const [tab, setTab] = useState('lama');
  const [monitor, setMonitor] = useState({ poli: [], total_menunggu: 0 });
  const [loadingMonitor, setLoadingMonitor] = useState(true);

  // Pasien Lama state
  const [identitas, setIdentitas] = useState('');
  const [tglLahirLama, setTglLahirLama] = useState('');
  const [poliLama, setPoliLama] = useState('Poli Umum');

  // Pasien Baru state
  const [newForm, setNewForm] = useState(EMPTY_NEW_PATIENT);

  // Cek Status state
  const [cekIdentitas, setCekIdentitas] = useState('');
  const [cekTglLahir, setCekTglLahir] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [activeTicket, setActiveTicket] = useState(null);

  const loadMonitor = useCallback(async () => {
    try {
      const data = await api.getPublicMonitor();
      setMonitor(data);
    } catch {
      // Abaikan gangguan sementara pada polling monitor
    } finally {
      setLoadingMonitor(false);
    }
  }, []);

  useEffect(() => {
    loadMonitor();
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/updates`;
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = () => loadMonitor();
    } catch {
      // Fallback polling
    }
    const timer = setInterval(loadMonitor, 10000);
    return () => {
      clearInterval(timer);
      if (ws && ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, [loadMonitor]);

  const handleTabChange = (nextTab) => {
    setTab(nextTab);
    setErrorMsg('');
  };

  const handleSubmitLama = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSubmitting(true);
    try {
      const ticket = await api.ambilAntreanPasienLama({
        identitas: identitas.trim(),
        tanggal_lahir: tglLahirLama,
        poli_tujuan: poliLama,
      });
      setActiveTicket(ticket);
      await loadMonitor();
      if (ticket.sudah_terdaftar_hari_ini) {
        onNotify(
          `Anda sudah memiliki antrean aktif (${ticket.nomor_antrean}). Tiket Anda ditampilkan kembali.`,
          'info'
        );
      } else {
        onNotify(
          `Nomor antrean ${ticket.nomor_antrean} (${ticket.poli_tujuan}) berhasil diterbitkan.`,
          'success'
        );
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitBaru = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSubmitting(true);
    try {
      const ticket = await api.ambilAntreanPasienBaru({
        ...newForm,
        nik: newForm.nik.trim(),
        nama: newForm.nama.trim(),
      });
      setActiveTicket(ticket);
      setNewForm(EMPTY_NEW_PATIENT);
      await loadMonitor();
      onNotify(
        `Registrasi berhasil! NRM ${ticket.pasien_nomor_rm} & antrean ${ticket.nomor_antrean} diterbitkan.`,
        'success'
      );
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCekStatus = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSubmitting(true);
    try {
      const ticket = await api.cekAntreanPasien(cekIdentitas.trim(), cekTglLahir);
      setActiveTicket(ticket);
      onNotify(`Antrean aktif ditemukan: ${ticket.nomor_antrean}.`, 'success');
    } catch (err) {
      setActiveTicket(null);
      setErrorMsg(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', color: 'var(--text-primary)' }}>
      {/* Header Publik */}
      <header className="top-header no-print">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Activity size={22} color="var(--primary)" />
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, letterSpacing: '0.03em' }}>
              MEDIKACARE — ANJUNGAN ANTREAN PASIEN
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Klinik Pratama Sehat • Ambil Nomor Antrean Mandiri Tanpa Akun
            </div>
          </div>
        </div>

        <div className="header-right">
          <button type="button" className="btn btn-outline btn-sm" onClick={onToggleTheme}>
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
          </button>
          <button type="button" className="btn btn-outline btn-sm" onClick={onBackToLogin}>
            <ArrowLeft size={15} />
            Login Staf Klinik
          </button>
        </div>
      </header>

      <main className="content-container" style={{ maxWidth: 1260 }}>
        {/* Papan Monitor Antrean Real-Time */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Clock size={17} color="var(--primary)" />
              Papan Monitor Antrean Ruang Tunggu (Real-Time)
            </h3>
            <span className="badge badge-primary">
              Total Menunggu: {monitor.total_menunggu} Pasien
            </span>
          </div>

          <div
            className="kpi-grid"
            style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', marginBottom: 0 }}
          >
            {loadingMonitor && monitor.poli.length === 0 ? (
              <div className="kpi-card">Memuat status antrean poli...</div>
            ) : (
              monitor.poli.map((p) => (
                <div key={p.poli_tujuan} className="kpi-card teal">
                  <div className="kpi-label">
                    <span style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {p.poli_tujuan}
                    </span>
                    <span className="badge badge-warning">{p.jumlah_menunggu} Menunggu</span>
                  </div>

                  <div
                    className="mono"
                    style={{
                      fontSize: 28,
                      fontWeight: 800,
                      color: p.sedang_dipanggil ? 'var(--teal)' : 'var(--text-muted)',
                    }}
                  >
                    {p.sedang_dipanggil ? p.sedang_dipanggil.nomor_antrean : 'Menunggu'}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {p.sedang_dipanggil
                      ? `Sedang diperiksa: ${p.sedang_dipanggil.nama_samaran}`
                      : 'Belum ada pasien di ruang periksa'}
                  </div>

                  {p.berikutnya.length > 0 && (
                    <div
                      style={{
                        marginTop: 10,
                        paddingTop: 8,
                        borderTop: '1px solid var(--border-color)',
                        fontSize: 12,
                        color: 'var(--text-muted)',
                      }}
                    >
                      Berikutnya:{' '}
                      {p.berikutnya.map((b) => b.nomor_antrean).join(', ')}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="grid-split">
          {/* Panel Kiri: Formulir Ambil Antrean Mandiri */}
          <div className="card" style={{ alignSelf: 'start' }}>
            <div className="card-header">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className={`btn btn-sm ${tab === 'lama' ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => handleTabChange('lama')}
                >
                  <Users size={14} />
                  Pasien Lama
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${tab === 'baru' ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => handleTabChange('baru')}
                >
                  <UserPlus size={14} />
                  Pasien Baru
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${tab === 'cek' ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => handleTabChange('cek')}
                >
                  <Search size={14} />
                  Cek Status Antrean
                </button>
              </div>
            </div>

            <div className="card-body">
              {errorMsg && (
                <div className="alert alert-danger" style={{ marginBottom: 14 }} role="alert">
                  <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
                  <span>{errorMsg}</span>
                </div>
              )}

              {tab === 'lama' && (
                <form onSubmit={handleSubmitLama} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div className="alert alert-info">
                    <span>
                      Verifikasi tanpa kata sandi: masukkan <strong>NIK (16 digit)</strong> atau{' '}
                      <strong>Nomor RM</strong> beserta <strong>Tanggal Lahir</strong> Anda. Prioritas Lansia (≥ 60 tahun) terdeteksi otomatis.
                    </span>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="public-identitas">
                      NIK (16 Digit) atau Nomor Rekam Medis (NRM)
                    </label>
                    <input
                      id="public-identitas"
                      type="text"
                      className="form-control mono"
                      placeholder="Contoh: 3526014508950002 atau RM-2026-0002"
                      value={identitas}
                      onChange={(e) => setIdentitas(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-grid">
                    <div className="form-group">
                      <label className="form-label" htmlFor="public-dob-lama">
                        Tanggal Lahir
                      </label>
                      <input
                        id="public-dob-lama"
                        type="date"
                        className="form-control"
                        value={tglLahirLama}
                        onChange={(e) => setTglLahirLama(e.target.value)}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label" htmlFor="public-poli-lama">
                        Poli Tujuan
                      </label>
                      <select
                        id="public-poli-lama"
                        className="form-control"
                        value={poliLama}
                        onChange={(e) => setPoliLama(e.target.value)}
                      >
                        <option value="Poli Umum">Poli Umum</option>
                        <option value="Poli Gigi">Poli Gigi</option>
                        <option value="Poli Anak">Poli Anak</option>
                      </select>
                    </div>
                  </div>

                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    <Ticket size={16} />
                    {submitting ? 'Memverifikasi & Menerbitkan Tiket...' : 'Ambil Nomor Antrean'}
                  </button>

                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    Contoh uji cepat: NRM <code className="mono">RM-2026-0002</code>, Tgl Lahir{' '}
                    <code className="mono">1995-08-05</code> (Siti Aminah) atau{' '}
                    <code className="mono">RM-2026-0005</code>, Tgl Lahir{' '}
                    <code className="mono">1958-07-09</code> (Lansia).
                  </div>
                </form>
              )}

              {tab === 'baru' && (
                <form onSubmit={handleSubmitBaru} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div className="alert alert-info">
                    <span>
                      Belum pernah berobat di Klinik Pratama Sehat? Isi data identitas Anda untuk mendapatkan Nomor RM sekaligus tiket antrean.
                    </span>
                  </div>

                  <div className="form-grid">
                    <div className="form-group full">
                      <label className="form-label">NIK (16 Digit Angka Valid)</label>
                      <input
                        type="text"
                        maxLength={16}
                        className="form-control mono"
                        placeholder="3526xxxxxxxxxxxx"
                        value={newForm.nik}
                        onChange={(e) => setNewForm({ ...newForm, nik: e.target.value })}
                        required
                      />
                    </div>

                    <div className="form-group full">
                      <label className="form-label">Nama Lengkap</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Nama sesuai KTP / KK"
                        value={newForm.nama}
                        onChange={(e) => setNewForm({ ...newForm, nama: e.target.value })}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Tanggal Lahir</label>
                      <input
                        type="date"
                        className="form-control"
                        value={newForm.tanggal_lahir}
                        onChange={(e) => setNewForm({ ...newForm, tanggal_lahir: e.target.value })}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Jenis Kelamin</label>
                      <select
                        className="form-control"
                        value={newForm.jenis_kelamin}
                        onChange={(e) => setNewForm({ ...newForm, jenis_kelamin: e.target.value })}
                      >
                        <option value="Laki-laki">Laki-laki</option>
                        <option value="Perempuan">Perempuan</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Poli Tujuan</label>
                      <select
                        className="form-control"
                        value={newForm.poli_tujuan}
                        onChange={(e) => setNewForm({ ...newForm, poli_tujuan: e.target.value })}
                      >
                        <option value="Poli Umum">Poli Umum</option>
                        <option value="Poli Gigi">Poli Gigi</option>
                        <option value="Poli Anak">Poli Anak</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">No. Telepon / HP</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="0812xxxxxxxx"
                        value={newForm.no_telepon}
                        onChange={(e) => setNewForm({ ...newForm, no_telepon: e.target.value })}
                      />
                    </div>

                    <div className="form-group full">
                      <label className="form-label">Riwayat Alergi Obat / Makanan</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Tidak ada / Penisilin / dll"
                        value={newForm.riwayat_alergi}
                        onChange={(e) => setNewForm({ ...newForm, riwayat_alergi: e.target.value })}
                      />
                    </div>

                    <div className="form-group full">
                      <label className="form-label">Alamat</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Alamat tempat tinggal"
                        value={newForm.alamat}
                        onChange={(e) => setNewForm({ ...newForm, alamat: e.target.value })}
                      />
                    </div>
                  </div>

                  <button type="submit" className="btn btn-success" disabled={submitting}>
                    <UserPlus size={16} />
                    {submitting ? 'Mendaftarkan...' : 'Daftar Pasien Baru & Ambil Antrean'}
                  </button>
                </form>
              )}

              {tab === 'cek' && (
                <form onSubmit={handleCekStatus} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div className="alert alert-info">
                    <span>
                      Masukkan NIK atau Nomor RM beserta Tanggal Lahir untuk melihat status antrean aktif Anda hari ini.
                    </span>
                  </div>
                  <div className="form-group">
                    <label className="form-label">NIK atau Nomor RM</label>
                    <input
                      type="text"
                      className="form-control mono"
                      placeholder="NIK 16 digit atau RM-2026-xxxx"
                      value={cekIdentitas}
                      onChange={(e) => setCekIdentitas(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tanggal Lahir</label>
                    <input
                      type="date"
                      className="form-control"
                      value={cekTglLahir}
                      onChange={(e) => setCekTglLahir(e.target.value)}
                      required
                    />
                  </div>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    <Search size={16} />
                    {submitting ? 'Mencari...' : 'Cek Status Antrean Saya'}
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Panel Kanan: Tiket Antrean Digital Pasien */}
          <div className="card" style={{ alignSelf: 'start' }}>
            <div className="card-header">
              <h3 className="card-title">
                <ClipboardCheck size={17} color="var(--success)" />
                Tiket Antrean Digital Anda
              </h3>
            </div>

            <div className="card-body">
              {!activeTicket ? (
                <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted)' }}>
                  <Ticket size={40} style={{ opacity: 0.45, marginBottom: 10 }} />
                  <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
                    Belum ada tiket ditampilkan
                  </div>
                  <div style={{ fontSize: 13 }}>
                    Silakan ambil nomor antrean pada formulir di sebelah kiri untuk melihat tiket dan perkiraan urutan Anda.
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center' }}>
                  {activeTicket.sudah_terdaftar_hari_ini && (
                    <div className="alert alert-warning" style={{ marginBottom: 14, textAlign: 'left' }}>
                      <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
                      <span>
                        Anda sudah memiliki antrean aktif hari ini. Sistem menampilkan tiket aktif Anda agar tidak terjadi antrean ganda.
                      </span>
                    </div>
                  )}

                  {!activeTicket.sudah_terdaftar_hari_ini && (
                    <div className="alert alert-success" style={{ marginBottom: 14, textAlign: 'left' }}>
                      <CheckCircle2 size={16} style={{ flexShrink: 0, marginTop: 1 }} />
                      <span>Tiket antrean berhasil diterbitkan dan masuk ke sistem klinik.</span>
                    </div>
                  )}

                  <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    {activeTicket.poli_tujuan}
                  </div>
                  <div
                    className="mono"
                    style={{
                      fontSize: 48,
                      fontWeight: 800,
                      color: 'var(--primary)',
                      margin: '6px 0',
                    }}
                  >
                    {activeTicket.nomor_antrean}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 16 }}>
                    <span className={`badge ${statusAntreanBadge(activeTicket.status)}`}>
                      Status: {activeTicket.status}
                    </span>
                    <span className={`badge ${prioritasBadge(activeTicket.prioritas)}`}>
                      {activeTicket.prioritas}
                    </span>
                  </div>

                  <div
                    style={{
                      textAlign: 'left',
                      background: 'var(--bg-surface-alt)',
                      padding: 14,
                      borderRadius: 12,
                      border: '1px solid var(--border-color)',
                      fontSize: 13.5,
                      lineHeight: 1.8,
                      marginBottom: 16,
                    }}
                  >
                    <div>
                      <strong>Nama Pasien:</strong> {activeTicket.pasien_nama}
                    </div>
                    <div>
                      <strong>Nomor Rekam Medis:</strong>{' '}
                      <span className="mono">{activeTicket.pasien_nomor_rm}</span>
                    </div>
                    <div>
                      <strong>Waktu Daftar:</strong> {formatWaktu(activeTicket.waktu_daftar)}
                    </div>
                    <div>
                      <strong>Antrean di Depan Anda:</strong>{' '}
                      <strong style={{ color: 'var(--primary)' }}>
                        {activeTicket.status === 'Diperiksa'
                          ? 'Sedang Dipanggil / Diperiksa Sekarang'
                          : `${activeTicket.antrean_di_depan} Pasien`}
                      </strong>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ width: '100%' }}
                    onClick={() => onPrintTicket(activeTicket)}
                  >
                    <Printer size={16} />
                    Cetak / Simpan Tiket Antrean
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
