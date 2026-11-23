import React, { useState } from 'react';
import { BellRing, ClipboardList, Printer, Ticket } from 'lucide-react';
import { api } from '../services/api';
import {
  formatJam,
  prioritasBadge,
  statusAntreanBadge,
} from '../utils/formatters';

export default function AntreanPage({
  user,
  antreanList,
  pasienList,
  onRefresh,
  onNotify,
  onPrintTicket,
  onPanggilBerikutnya,
  busyAction,
}) {
  const [poliFilter, setPoliFilter] = useState('Semua');
  const [selectedRm, setSelectedRm] = useState('');
  const [poliDaftar, setPoliDaftar] = useState('Poli Umum');
  const [prioritas, setPrioritas] = useState('Reguler');
  const [submitting, setSubmitting] = useState(false);

  const activePatients = pasienList.filter((p) => p.aktif);
  const filteredQueue =
    poliFilter === 'Semua'
      ? antreanList
      : antreanList.filter((a) => a.poli_tujuan === poliFilter);

  const handleDaftar = async (e) => {
    e.preventDefault();
    if (!selectedRm) {
      onNotify('Pilih pasien terlebih dahulu.', 'error');
      return;
    }
    setSubmitting(true);
    try {
      const ticket = await api.daftarAntrean({
        pasien_nomor_rm: selectedRm,
        poli_tujuan: poliDaftar,
        prioritas,
      });
      onNotify(
        `Antrean ${ticket.nomor_antrean} (${ticket.poli_tujuan}) berhasil diterbitkan.`,
        'success'
      );
      setSelectedRm('');
      await onRefresh();
      onPrintTicket(ticket);
    } catch (err) {
      onNotify(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Kartu Nomor Antrean Terakhir / Sedang Dipanggil per Poli */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', marginBottom: 0 }}>
        {['Poli Umum', 'Poli Gigi', 'Poli Anak'].map((poli) => {
          const aktif = antreanList.find(
            (a) => a.poli_tujuan === poli && a.status === 'Diperiksa'
          );
          const menungguCount = antreanList.filter(
            (a) => a.poli_tujuan === poli && a.status === 'Menunggu'
          ).length;
          return (
            <div key={poli} className="kpi-card teal">
              <div className="kpi-label">
                <span>{poli}</span>
                <span className="badge badge-warning">{menungguCount} Menunggu</span>
              </div>
              <div className="kpi-value mono">
                {aktif ? aktif.nomor_antrean : 'Kosong'}
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 4 }}>
                {aktif ? `Sedang diperiksa: ${aktif.pasien_nama}` : 'Belum ada pasien dipanggil'}
              </div>
            </div>
          );
        })}
      </div>

      <div className={user.peran === 'PetugasAdministrasi' ? 'grid-split' : ''}>
        {user.peran === 'PetugasAdministrasi' && (
          <div className="card" style={{ alignSelf: 'start' }}>
            <div className="card-header">
              <h3 className="card-title">
                <Ticket size={17} color="var(--primary)" />
                Registrasi Antrean Poli
              </h3>
            </div>
            <form onSubmit={handleDaftar} className="card-body">
              <div className="form-group" style={{ marginBottom: 14 }}>
                <label className="form-label">Pilih Pasien Terdaftar</label>
                <select
                  className="form-control"
                  value={selectedRm}
                  onChange={(e) => setSelectedRm(e.target.value)}
                  required
                >
                  <option value="">-- Pilih Pasien (NRM / Nama) --</option>
                  {activePatients.map((p) => (
                    <option key={p.nomor_rm} value={p.nomor_rm}>
                      {p.nomor_rm} — {p.nama} ({p.umur} thn)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 14 }}>
                <label className="form-label">Poli Tujuan</label>
                <select
                  className="form-control"
                  value={poliDaftar}
                  onChange={(e) => setPoliDaftar(e.target.value)}
                >
                  <option value="Poli Umum">Poli Umum</option>
                  <option value="Poli Gigi">Poli Gigi</option>
                  <option value="Poli Anak">Poli Anak</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 16 }}>
                <label className="form-label">Kategori Antrean (FIFO / Prioritas)</label>
                <select
                  className="form-control"
                  value={prioritas}
                  onChange={(e) => setPrioritas(e.target.value)}
                >
                  <option value="Reguler">Reguler (FIFO)</option>
                  <option value="Lansia">Lansia (Prioritas)</option>
                  <option value="Darurat">Darurat (Prioritas Utama)</option>
                </select>
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={submitting}>
                <Ticket size={16} />
                {submitting ? 'Memproses...' : 'Terbitkan Nomor Antrean'}
              </button>
            </form>
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <ClipboardList size={17} color="var(--primary)" />
              Daftar Antrean Terpadu ({filteredQueue.length})
            </h3>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              {['Semua', 'Poli Umum', 'Poli Gigi', 'Poli Anak'].map((poli) => (
                <button
                  key={poli}
                  type="button"
                  className={`btn btn-sm ${poliFilter === poli ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => setPoliFilter(poli)}
                >
                  {poli}
                </button>
              ))}
              {user.peran === 'Dokter' && (
                <button
                  type="button"
                  className="btn btn-success btn-sm"
                  disabled={busyAction}
                  onClick={() =>
                    onPanggilBerikutnya(poliFilter === 'Semua' ? user.poli_praktik || '' : poliFilter)
                  }
                >
                  <BellRing size={14} />
                  Panggil Berikutnya
                </button>
              )}
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nomor</th>
                  <th>Pasien</th>
                  <th>Poli Tujuan</th>
                  <th>Prioritas</th>
                  <th>Jam Daftar</th>
                  <th>Status</th>
                  <th>Tiket</th>
                </tr>
              </thead>
              <tbody>
                {filteredQueue.map((item) => (
                  <tr key={item.id}>
                    <td className="mono" style={{ fontWeight: 800, fontSize: 14 }}>
                      {item.nomor_antrean}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{item.pasien_nama}</div>
                      <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                        {item.pasien_nomor_rm}
                      </div>
                    </td>
                    <td>{item.poli_tujuan}</td>
                    <td>
                      <span className={`badge ${prioritasBadge(item.prioritas)}`}>
                        {item.prioritas}
                      </span>
                    </td>
                    <td>{formatJam(item.waktu_daftar)}</td>
                    <td>
                      <span className={`badge ${statusAntreanBadge(item.status)}`}>
                        {item.status}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => onPrintTicket(item)}
                      >
                        <Printer size={13} />
                        Tiket
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredQueue.length === 0 && (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                      Tidak ada antrean untuk filter ini.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
