import React, { useState } from 'react';
import { CheckCircle2, Edit3, PackagePlus, Pill } from 'lucide-react';
import { api } from '../services/api';
import { formatRupiah, formatTanggalIndo } from '../utils/formatters';

const EMPTY_OBAT = {
  nama_obat: '',
  stok: 50,
  harga_satuan: 5000,
  satuan: 'Strip',
  kategori: 'Umum',
};

export default function FarmasiPage({
  resepList,
  obatList,
  onRefresh,
  onNotify,
}) {
  const [obatForm, setObatForm] = useState(EMPTY_OBAT);
  const [editingKode, setEditingKode] = useState(null);
  const [validatingId, setValidatingId] = useState(null);
  const [savingObat, setSavingObat] = useState(false);

  const handleValidasiResep = async (idRekamMedis) => {
    setValidatingId(idRekamMedis);
    try {
      await api.validasiResep(idRekamMedis);
      onNotify(
        `Resep ${idRekamMedis} divalidasi dan stok inventaris obat telah diperbarui.`,
        'success'
      );
      await onRefresh();
    } catch (err) {
      onNotify(err.message, 'error');
    } finally {
      setValidatingId(null);
    }
  };

  const handleSaveObat = async (e) => {
    e.preventDefault();
    setSavingObat(true);
    try {
      const payload = {
        ...obatForm,
        stok: Number(obatForm.stok),
        harga_satuan: Number(obatForm.harga_satuan),
      };
      if (editingKode) {
        await api.updateObat(editingKode, payload);
        onNotify(`Data obat ${editingKode} diperbarui.`, 'success');
      } else {
        const created = await api.createObat(payload);
        onNotify(`Obat ${created.nama_obat} (${created.kode_obat}) ditambahkan.`, 'success');
      }
      setObatForm(EMPTY_OBAT);
      setEditingKode(null);
      await onRefresh();
    } catch (err) {
      onNotify(err.message, 'error');
    } finally {
      setSavingObat(false);
    }
  };

  const startEditObat = (o) => {
    setEditingKode(o.kode_obat);
    setObatForm({
      nama_obat: o.nama_obat,
      stok: o.stok,
      harga_satuan: o.harga_satuan,
      satuan: o.satuan,
      kategori: o.kategori,
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Antrean Validasi Resep Digital */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Pill size={17} color="var(--primary)" />
            Validasi Resep Obat Digital ({resepList.length})
          </h3>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {resepList.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13.5 }}>
              Belum ada resep obat digital masuk.
            </div>
          ) : (
            resepList.map((rm) => {
              const isDone = rm.status_resep === 'Divalidasi';
              return (
                <div
                  key={rm.id_rekam_medis}
                  style={{
                    border: '1px solid var(--border-color)',
                    borderRadius: 12,
                    padding: 16,
                    background: 'var(--bg-surface-alt)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: 12,
                      flexWrap: 'wrap',
                      marginBottom: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 14.5 }}>
                        {rm.pasien_nama}{' '}
                        <span className="mono" style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                          ({rm.pasien_nomor_rm})
                        </span>
                      </div>
                      <div style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                        ID: <span className="mono">{rm.id_rekam_medis}</span> • Dokter: {rm.dokter_nama} •{' '}
                        {formatTanggalIndo(rm.tanggal_periksa)}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span className={`badge ${isDone ? 'badge-success' : 'badge-warning'}`}>
                        {rm.status_resep}
                      </span>
                      {!isDone && (
                        <button
                          type="button"
                          className="btn btn-success btn-sm"
                          disabled={validatingId === rm.id_rekam_medis}
                          onClick={() => handleValidasiResep(rm.id_rekam_medis)}
                        >
                          <CheckCircle2 size={14} />
                          {validatingId === rm.id_rekam_medis
                            ? 'Memvalidasi...'
                            : 'Validasi & Siapkan Obat'}
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Kode</th>
                          <th>Nama Obat</th>
                          <th>Jumlah</th>
                          <th>Dosis / Aturan Pakai</th>
                          <th>Subtotal</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rm.resep.map((item) => (
                          <tr key={item.id}>
                            <td className="mono">{item.kode_obat}</td>
                            <td style={{ fontWeight: 600 }}>{item.nama_obat}</td>
                            <td>{item.jumlah_beli}</td>
                            <td>{item.dosis}</td>
                            <td style={{ fontWeight: 600 }}>{formatRupiah(item.subtotal)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Manajemen Inventaris Obat */}
      <div className="grid-split">
        <div className="card" style={{ alignSelf: 'start' }}>
          <div className="card-header">
            <h3 className="card-title">
              <PackagePlus size={17} color="var(--teal)" />
              {editingKode ? `Update Obat (${editingKode})` : 'Tambah Obat Baru'}
            </h3>
            {editingKode && (
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => {
                  setEditingKode(null);
                  setObatForm(EMPTY_OBAT);
                }}
              >
                Batal
              </button>
            )}
          </div>
          <form onSubmit={handleSaveObat} className="card-body">
            <div className="form-grid">
              <div className="form-group full">
                <label className="form-label">Nama Sediaan Obat</label>
                <input
                  type="text"
                  className="form-control"
                  value={obatForm.nama_obat}
                  onChange={(e) => setObatForm({ ...obatForm, nama_obat: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Stok Tersedia</label>
                <input
                  type="number"
                  min={0}
                  className="form-control"
                  value={obatForm.stok}
                  onChange={(e) => setObatForm({ ...obatForm, stok: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Harga Satuan (Rp)</label>
                <input
                  type="number"
                  min={0}
                  className="form-control"
                  value={obatForm.harga_satuan}
                  onChange={(e) => setObatForm({ ...obatForm, harga_satuan: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Satuan</label>
                <input
                  type="text"
                  className="form-control"
                  value={obatForm.satuan}
                  onChange={(e) => setObatForm({ ...obatForm, satuan: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Kategori</label>
                <input
                  type="text"
                  className="form-control"
                  value={obatForm.kategori}
                  onChange={(e) => setObatForm({ ...obatForm, kategori: e.target.value })}
                />
              </div>
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 16 }}
              disabled={savingObat}
            >
              {savingObat ? 'Menyimpan...' : editingKode ? 'Simpan Perubahan Obat' : 'Tambahkan ke Inventaris'}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Katalog & Saldo Stok Obat ({obatList.length})</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Kode</th>
                  <th>Nama Obat</th>
                  <th>Kategori</th>
                  <th>Stok</th>
                  <th>Harga Satuan</th>
                  <th>Edit</th>
                </tr>
              </thead>
              <tbody>
                {obatList.map((o) => (
                  <tr key={o.kode_obat}>
                    <td className="mono">{o.kode_obat}</td>
                    <td style={{ fontWeight: 600 }}>{o.nama_obat}</td>
                    <td>{o.kategori}</td>
                    <td>
                      <span className={`badge ${o.stok <= 20 ? 'badge-danger' : 'badge-success'}`}>
                        {o.stok} {o.satuan}
                      </span>
                    </td>
                    <td>{formatRupiah(o.harga_satuan)}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        onClick={() => startEditObat(o)}
                      >
                        <Edit3 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
