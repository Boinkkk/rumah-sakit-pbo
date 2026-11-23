import React, { useState } from 'react';
import {
  AlertTriangle,
  Edit3,
  Plus,
  Search,
  Ticket,
  UserCheck,
  UserX,
} from 'lucide-react';
import { api } from '../services/api';

const EMPTY_FORM = {
  nik: '',
  nama: '',
  tanggal_lahir: '',
  jenis_kelamin: 'Laki-laki',
  alamat: '',
  no_telepon: '',
  riwayat_alergi: 'Tidak ada',
};

export default function PasienPage({
  pasienList,
  onRefresh,
  onNotify,
  onPrintTicket,
}) {
  const [search, setSearch] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingRm, setEditingRm] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [queueTarget, setQueueTarget] = useState(null);
  const [queuePoli, setQueuePoli] = useState('Poli Umum');
  const [queuePrioritas, setQueuePrioritas] = useState('Reguler');

  const filtered = pasienList.filter((p) => {
    if (!showInactive && !p.aktif) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      p.nama.toLowerCase().includes(q) ||
      p.nik.includes(q) ||
      p.nomor_rm.toLowerCase().includes(q)
    );
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingRm) {
        await api.updatePasien(editingRm, form);
        onNotify(`Data pasien ${form.nama} (${editingRm}) berhasil diperbarui.`, 'success');
      } else {
        const created = await api.createPasien(form);
        onNotify(
          `Pasien baru ${created.nama} terdaftar dengan NRM ${created.nomor_rm}.`,
          'success'
        );
      }
      setForm(EMPTY_FORM);
      setEditingRm(null);
      await onRefresh();
    } catch (err) {
      onNotify(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (p) => {
    setEditingRm(p.nomor_rm);
    setForm({
      nik: p.nik,
      nama: p.nama,
      tanggal_lahir: p.tanggal_lahir,
      jenis_kelamin: p.jenis_kelamin,
      alamat: p.alamat,
      no_telepon: p.no_telepon,
      riwayat_alergi: p.riwayat_alergi,
    });
  };

  const handleToggleActive = async (p) => {
    try {
      if (p.aktif) {
        await api.deactivatePasien(p.nomor_rm);
        onNotify(`Pasien ${p.nama} dinonaktifkan.`, 'success');
      } else {
        await api.updatePasien(p.nomor_rm, { aktif: true });
        onNotify(`Pasien ${p.nama} diaktifkan kembali.`, 'success');
      }
      await onRefresh();
    } catch (err) {
      onNotify(err.message, 'error');
    }
  };

  const handleRegisterQueue = async (e) => {
    e.preventDefault();
    if (!queueTarget) return;
    try {
      const ticket = await api.daftarAntrean({
        pasien_nomor_rm: queueTarget.nomor_rm,
        poli_tujuan: queuePoli,
        prioritas: queuePrioritas,
      });
      onNotify(
        `Tiket antrean ${ticket.nomor_antrean} diterbitkan untuk ${queueTarget.nama}.`,
        'success'
      );
      setQueueTarget(null);
      await onRefresh();
      onPrintTicket(ticket);
    } catch (err) {
      onNotify(err.message, 'error');
    }
  };

  return (
    <div className="grid-split">
      {/* Formulir Input / Edit Data Pasien */}
      <div className="card" style={{ alignSelf: 'start' }}>
        <div className="card-header">
          <h3 className="card-title">
            <Plus size={17} color="var(--primary)" />
            {editingRm ? `Edit Profil Pasien (${editingRm})` : 'Pendaftaran Pasien Baru'}
          </h3>
          {editingRm && (
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => {
                setEditingRm(null);
                setForm(EMPTY_FORM);
              }}
            >
              Batal Edit
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="card-body">
          <div className="form-grid">
            <div className="form-group full">
              <label className="form-label">NIK (16 Digit Angka Valid)</label>
              <input
                type="text"
                className="form-control mono"
                maxLength={16}
                placeholder="Contoh: 3526011205920001"
                value={form.nik}
                onChange={(e) => setForm({ ...form, nik: e.target.value })}
                required
              />
            </div>

            <div className="form-group full">
              <label className="form-label">Nama Lengkap Pasien</label>
              <input
                type="text"
                className="form-control"
                placeholder="Nama sesuai KTP / KK"
                value={form.nama}
                onChange={(e) => setForm({ ...form, nama: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Tanggal Lahir</label>
              <input
                type="date"
                className="form-control"
                value={form.tanggal_lahir}
                onChange={(e) => setForm({ ...form, tanggal_lahir: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Jenis Kelamin</label>
              <select
                className="form-control"
                value={form.jenis_kelamin}
                onChange={(e) => setForm({ ...form, jenis_kelamin: e.target.value })}
              >
                <option value="Laki-laki">Laki-laki</option>
                <option value="Perempuan">Perempuan</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">No. Telepon / HP</label>
              <input
                type="text"
                className="form-control"
                placeholder="0812xxxxxxxx"
                value={form.no_telepon}
                onChange={(e) => setForm({ ...form, no_telepon: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Riwayat Alergi Obat / Makanan</label>
              <input
                type="text"
                className="form-control"
                placeholder="Tidak ada / Penisilin / dll"
                value={form.riwayat_alergi}
                onChange={(e) => setForm({ ...form, riwayat_alergi: e.target.value })}
              />
            </div>

            <div className="form-group full">
              <label className="form-label">Alamat Lengkap</label>
              <textarea
                rows={2}
                className="form-control"
                placeholder="Alamat domisili pasien..."
                value={form.alamat}
                onChange={(e) => setForm({ ...form, alamat: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
            <button type="submit" className="btn btn-primary" disabled={submitting} style={{ flex: 1 }}>
              {submitting
                ? 'Menyimpan...'
                : editingRm
                ? 'Simpan Perubahan'
                : 'Simpan & Terbitkan NRM'}
            </button>
          </div>
        </form>
      </div>

      {/* Tabel Daftar Pasien */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Database Pasien ({filtered.length})</h3>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative' }}>
              <Search
                size={15}
                style={{
                  position: 'absolute',
                  left: 10,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                }}
              />
              <input
                type="text"
                className="form-control"
                style={{ paddingLeft: 32, width: 230 }}
                placeholder="Cari NRM, NIK, atau Nama..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <label style={{ fontSize: 12.5, display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
              />
              Tampilkan nonaktif
            </label>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>No. RM / NIK</th>
                <th>Nama & Usia</th>
                <th>Alergi</th>
                <th>Status</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.nomor_rm}>
                  <td>
                    <div className="mono" style={{ fontWeight: 700, fontSize: 12.5 }}>
                      {p.nomor_rm}
                    </div>
                    <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                      {p.nik}
                    </div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{p.nama}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {p.jenis_kelamin} • {p.umur} thn
                    </div>
                  </td>
                  <td>
                    {p.riwayat_alergi && p.riwayat_alergi.toLowerCase() !== 'tidak ada' ? (
                      <span className="badge badge-danger">
                        <AlertTriangle size={12} />
                        {p.riwayat_alergi}
                      </span>
                    ) : (
                      <span className="badge badge-muted">Tidak ada</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${p.aktif ? 'badge-success' : 'badge-muted'}`}>
                      {p.aktif ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {p.aktif && (
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          title="Daftarkan ke Antrean Poli"
                          onClick={() => setQueueTarget(p)}
                        >
                          <Ticket size={13} />
                          Antrean
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        title="Edit Data Pasien"
                        onClick={() => startEdit(p)}
                      >
                        <Edit3 size={13} />
                      </button>
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        title={p.aktif ? 'Nonaktifkan Pasien' : 'Aktifkan Pasien'}
                        onClick={() => handleToggleActive(p)}
                      >
                        {p.aktif ? <UserX size={13} /> : <UserCheck size={13} />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                    Data pasien tidak ditemukan.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Terbitkan Antrean Cepat */}
      {queueTarget && (
        <div className="modal-backdrop" onClick={() => setQueueTarget(null)}>
          <div
            className="modal-content"
            style={{ maxWidth: 440 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="card-header">
              <h3 className="card-title">Terbitkan Tiket Antrean Poli</h3>
            </div>
            <form onSubmit={handleRegisterQueue} className="card-body">
              <div className="alert alert-info" style={{ marginBottom: 14 }}>
                <div>
                  <strong>{queueTarget.nama}</strong> ({queueTarget.nomor_rm})
                </div>
              </div>
              <div className="form-group" style={{ marginBottom: 12 }}>
                <label className="form-label">Poli Tujuan</label>
                <select
                  className="form-control"
                  value={queuePoli}
                  onChange={(e) => setQueuePoli(e.target.value)}
                >
                  <option value="Poli Umum">Poli Umum</option>
                  <option value="Poli Gigi">Poli Gigi</option>
                  <option value="Poli Anak">Poli Anak</option>
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 18 }}>
                <label className="form-label">Tingkat Urgensi / Prioritas</label>
                <select
                  className="form-control"
                  value={queuePrioritas}
                  onChange={(e) => setQueuePrioritas(e.target.value)}
                >
                  <option value="Reguler">Reguler (FIFO)</option>
                  <option value="Lansia">Lansia (Prioritas)</option>
                  <option value="Darurat">Gawat Darurat (Prioritas Utama)</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setQueueTarget(null)}
                >
                  Batal
                </button>
                <button type="submit" className="btn btn-primary">
                  <Ticket size={15} />
                  Terbitkan & Cetak Tiket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
