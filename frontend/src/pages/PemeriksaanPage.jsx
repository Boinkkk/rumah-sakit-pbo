import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  BellRing,
  CheckCircle,
  History,
  Plus,
  RotateCcw,
  Stethoscope,
  Trash2,
} from 'lucide-react';
import { api } from '../services/api';
import { formatRupiah, formatTanggalIndo, statusAntreanBadge } from '../utils/formatters';

const TINDAKAN_PRESETS = [
  { kode_layanan: 'TND-01', nama_layanan: 'Pemeriksaan Fisik & Konsultasi Lanjutan', tarif_dasar: 25000, biaya_alat_habis_pakai: 5000 },
  { kode_layanan: 'TND-02', nama_layanan: 'Injeksi Vitamin / Obat', tarif_dasar: 30000, biaya_alat_habis_pakai: 15000 },
  { kode_layanan: 'TND-03', nama_layanan: 'Perawatan Luka & Ganti Perban', tarif_dasar: 40000, biaya_alat_habis_pakai: 20000 },
  { kode_layanan: 'TND-04', nama_layanan: 'Nebulizer Terapi Pernapasan', tarif_dasar: 45000, biaya_alat_habis_pakai: 25000 },
  { kode_layanan: 'TND-05', nama_layanan: 'Scaling / Pembersihan Karang Gigi', tarif_dasar: 120000, biaya_alat_habis_pakai: 30000 },
];

export default function PemeriksaanPage({
  user,
  antreanList,
  obatList,
  onRefresh,
  onNotify,
  onPanggilBerikutnya,
  busyAction,
}) {
  const [poliChoice, setPoliChoice] = useState(user.poli_praktik || '');
  const activeAntrean = antreanList.find(
    (a) => a.status === 'Diperiksa' && (!poliChoice || a.poli_tujuan === poliChoice)
  );

  const [history, setHistory] = useState([]);
  const [keluhan, setKeluhan] = useState('');
  const [tekananDarah, setTekananDarah] = useState('120/80 mmHg');
  const [suhuTubuh, setSuhuTubuh] = useState('36.8');
  const [denyutNadi, setDenyutNadi] = useState('80');
  const [diagnosis, setDiagnosis] = useState('');
  const [catatan, setCatatan] = useState('');
  const [tindakanItems, setTindakanItems] = useState([]);
  const [resepItems, setResepItems] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState(TINDAKAN_PRESETS[0].kode_layanan);
  const [selectedObat, setSelectedObat] = useState('');
  const [jumlahObat, setJumlahObat] = useState(1);
  const [dosisObat, setDosisObat] = useState('3x1 sesudah makan');
  const [biayaRacik, setBiayaRacik] = useState('0');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (obatList.length > 0 && !selectedObat) {
      setSelectedObat(obatList[0].kode_obat);
    }
  }, [obatList, selectedObat]);

  useEffect(() => {
    let ignore = false;
    async function loadHistory() {
      if (!activeAntrean?.pasien_nomor_rm) {
        setHistory([]);
        return;
      }
      try {
        const res = await api.listRekamMedisPasien(activeAntrean.pasien_nomor_rm);
        if (!ignore) setHistory(res);
      } catch {
        if (!ignore) setHistory([]);
      }
    }
    loadHistory();
    return () => {
      ignore = true;
    };
  }, [activeAntrean?.pasien_nomor_rm]);

  const resetForm = () => {
    setKeluhan('');
    setTekananDarah('120/80 mmHg');
    setSuhuTubuh('36.8');
    setDenyutNadi('80');
    setDiagnosis('');
    setCatatan('');
    setTindakanItems([]);
    setResepItems([]);
  };

  const addPresetTindakan = () => {
    const preset = TINDAKAN_PRESETS.find((p) => p.kode_layanan === selectedPreset);
    if (!preset) return;
    setTindakanItems([...tindakanItems, { ...preset }]);
  };

  const addResepItem = () => {
    const obat = obatList.find((o) => o.kode_obat === selectedObat);
    if (!obat) return;
    const qty = Math.max(1, Number(jumlahObat) || 1);
    if (qty > obat.stok) {
      onNotify(`Stok ${obat.nama_obat} hanya tersisa ${obat.stok}.`, 'error');
      return;
    }
    setResepItems([
      ...resepItems,
      {
        kode_obat: obat.kode_obat,
        nama_obat: obat.nama_obat,
        harga_satuan: obat.harga_satuan,
        jumlah_beli: qty,
        dosis: dosisObat || '3x1 sesudah makan',
        biaya_racik: Math.max(0, Number(biayaRacik) || 0),
      },
    ]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!activeAntrean) {
      onNotify('Panggil antrean pasien terlebih dahulu.', 'error');
      return;
    }
    setSubmitting(true);
    try {
      const created = await api.createRekamMedis({
        pasien_nomor_rm: activeAntrean.pasien_nomor_rm,
        antrean_id: activeAntrean.id,
        keluhan_utama: keluhan,
        tekanan_darah: tekananDarah,
        suhu_tubuh: Number(suhuTubuh),
        denyut_nadi: Number(denyutNadi),
        diagnosis,
        catatan_dokter: catatan,
        tindakan: tindakanItems,
        resep: resepItems.map((r) => ({
          kode_obat: r.kode_obat,
          jumlah_beli: r.jumlah_beli,
          dosis: r.dosis,
          biaya_racik: r.biaya_racik,
        })),
      });
      onNotify(
        `Rekam medis ${created.id_rekam_medis} tersimpan & dirujuk ke Farmasi/Kasir.`,
        'success'
      );
      resetForm();
      await onRefresh();
    } catch (err) {
      onNotify(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const waitingForPoli = antreanList.filter(
    (a) => a.status === 'Menunggu' && (!poliChoice || a.poli_tujuan === poliChoice)
  );

  return (
    <div className="grid-split">
      {/* Kolom Kiri: Antrean Poli & Riwayat Medis Pasien */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Kontrol Antrean Ruang Periksa</h3>
            <select
              className="form-control"
              style={{ width: 150 }}
              value={poliChoice}
              onChange={(e) => setPoliChoice(e.target.value)}
            >
              <option value="">Semua Poli</option>
              <option value="Poli Umum">Poli Umum</option>
              <option value="Poli Gigi">Poli Gigi</option>
              <option value="Poli Anak">Poli Anak</option>
            </select>
          </div>
          <div className="card-body">
            {activeAntrean ? (
              <div className="alert alert-success" style={{ marginBottom: 14 }}>
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong className="mono" style={{ fontSize: 18 }}>
                      {activeAntrean.nomor_antrean} — {activeAntrean.pasien_nama}
                    </strong>
                    <span className="badge badge-teal">{activeAntrean.poli_tujuan}</span>
                  </div>
                  <div style={{ fontSize: 12.5, marginTop: 4 }}>
                    NRM: <span className="mono">{activeAntrean.pasien_nomor_rm}</span>
                  </div>
                  {activeAntrean.riwayat_alergi &&
                    activeAntrean.riwayat_alergi.toLowerCase() !== 'tidak ada' && (
                      <div
                        style={{
                          marginTop: 8,
                          padding: '6px 10px',
                          borderRadius: 7,
                          background: 'var(--danger-soft)',
                          color: 'var(--danger)',
                          fontWeight: 700,
                          fontSize: 12.5,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        <AlertTriangle size={14} />
                        PERINGATAN ALERGI: {activeAntrean.riwayat_alergi}
                      </div>
                    )}
                </div>
              </div>
            ) : (
              <div className="alert alert-warning" style={{ marginBottom: 14 }}>
                <span>Belum ada pasien yang sedang diperiksa.</span>
              </div>
            )}

            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={busyAction || Boolean(activeAntrean)}
              onClick={() => onPanggilBerikutnya(poliChoice)}
            >
              <BellRing size={16} />
              [PANGGIL ANTREAN BERIKUTNYA] ({waitingForPoli.length} Menunggu)
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>No</th>
                  <th>Pasien</th>
                  <th>Prioritas</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {antreanList
                  .filter((a) => !poliChoice || a.poli_tujuan === poliChoice)
                  .slice(0, 6)
                  .map((a) => (
                    <tr key={a.id}>
                      <td className="mono" style={{ fontWeight: 700 }}>{a.nomor_antrean}</td>
                      <td>{a.pasien_nama}</td>
                      <td><span className="badge badge-muted">{a.prioritas}</span></td>
                      <td>
                        <span className={`badge ${statusAntreanBadge(a.status)}`}>{a.status}</span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Kartu Ringkasan Riwayat Rekam Medis Pasien */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <History size={17} color="var(--primary)" />
              Riwayat Medis Pasien
            </h3>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {!activeAntrean ? (
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Panggil pasien untuk melihat riwayat diagnosis sebelumnya.
              </div>
            ) : history.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Pasien belum memiliki catatan rekam medis sebelumnya (kunjungan pertama).
              </div>
            ) : (
              history.map((rm) => (
                <div
                  key={rm.id_rekam_medis}
                  style={{
                    padding: 12,
                    borderRadius: 10,
                    background: 'var(--bg-surface-alt)',
                    border: '1px solid var(--border-color)',
                    fontSize: 12.5,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <strong>{rm.diagnosis}</strong>
                    <span style={{ color: 'var(--text-muted)' }}>
                      {formatTanggalIndo(rm.tanggal_periksa)}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>Keluhan: {rm.keluhan_utama}</div>
                  <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                    TD: {rm.tekanan_darah} • Suhu: {rm.suhu_tubuh}°C • Dokter: {rm.dokter_nama}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Kolom Kanan: Formulir Pemeriksaan Medis & Resep Digital */}
      <div className="card" style={{ alignSelf: 'start' }}>
        <div className="card-header">
          <h3 className="card-title">
            <Stethoscope size={17} color="var(--teal)" />
            {activeAntrean
              ? `Pemeriksaan Medis (${activeAntrean.pasien_nama} - ${activeAntrean.nomor_antrean})`
              : 'Formulir Rekam Medis & Peresepan Digital'}
          </h3>
        </div>

        <form onSubmit={handleSubmit} className="card-body">
          <div className="form-grid">
            <div className="form-group full">
              <label className="form-label">Keluhan Utama (Anamnesis)</label>
              <textarea
                rows={2}
                className="form-control"
                placeholder="Contoh: Demam tinggi sejak 3 hari, pusing dan mual..."
                value={keluhan}
                onChange={(e) => setKeluhan(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Tekanan Darah</label>
              <input
                type="text"
                className="form-control"
                value={tekananDarah}
                onChange={(e) => setTekananDarah(e.target.value)}
                required
              />
            </div>

            <div className="form-grid" style={{ gap: 10 }}>
              <div className="form-group">
                <label className="form-label">Suhu (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  className="form-control"
                  value={suhuTubuh}
                  onChange={(e) => setSuhuTubuh(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Nadi (bpm)</label>
                <input
                  type="number"
                  className="form-control"
                  value={denyutNadi}
                  onChange={(e) => setDenyutNadi(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group full">
              <label className="form-label">Diagnosis Terstandar (ICD-10)</label>
              <input
                type="text"
                className="form-control"
                placeholder="Contoh: A09 - Gastroenteritis Akut & Febris"
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                required
              />
            </div>

            <div className="form-group full">
              <label className="form-label">Catatan Klinis Dokter (Opsional)</label>
              <input
                type="text"
                className="form-control"
                placeholder="Anjuran istirahat / kontrol ulang..."
                value={catatan}
                onChange={(e) => setCatatan(e.target.value)}
              />
            </div>
          </div>

          {/* Tindakan Medis */}
          <div style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--border-color)' }}>
            <label className="form-label" style={{ display: 'block', marginBottom: 8 }}>
              Tindakan Medis (Komponen LayananKlinik)
            </label>
            <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
              <select
                className="form-control"
                value={selectedPreset}
                onChange={(e) => setSelectedPreset(e.target.value)}
              >
                {TINDAKAN_PRESETS.map((p) => (
                  <option key={p.kode_layanan} value={p.kode_layanan}>
                    {p.nama_layanan} ({formatRupiah(p.tarif_dasar + p.biaya_alat_habis_pakai)})
                  </option>
                ))}
              </select>
              <button type="button" className="btn btn-outline" onClick={addPresetTindakan}>
                <Plus size={15} />
                Tambah
              </button>
            </div>
            {tindakanItems.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {tindakanItems.map((t, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      borderRadius: 8,
                      background: 'var(--bg-surface-alt)',
                      fontSize: 13,
                    }}
                  >
                    <span>
                      <strong>{t.nama_layanan}</strong> ({formatRupiah(t.tarif_dasar + t.biaya_alat_habis_pakai)})
                    </span>
                    <button
                      type="button"
                      className="btn btn-outline btn-sm"
                      onClick={() => setTindakanItems(tindakanItems.filter((_, i) => i !== idx))}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Resep Obat Digital */}
          <div style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--border-color)' }}>
            <label className="form-label" style={{ display: 'block', marginBottom: 8 }}>
              Resep Obat Digital (Dikirim ke Farmasi & Kasir)
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 0.6fr 1.2fr 0.7fr auto', gap: 8, marginBottom: 10 }}>
              <select
                className="form-control"
                value={selectedObat}
                onChange={(e) => setSelectedObat(e.target.value)}
              >
                {obatList.map((o) => (
                  <option key={o.kode_obat} value={o.kode_obat} disabled={o.stok === 0}>
                    {o.nama_obat} (Stok: {o.stok} | {formatRupiah(o.harga_satuan)})
                  </option>
                ))}
              </select>
              <input
                type="number"
                min={1}
                className="form-control"
                placeholder="Qty"
                value={jumlahObat}
                onChange={(e) => setJumlahObat(e.target.value)}
              />
              <input
                type="text"
                className="form-control"
                placeholder="Dosis pakai"
                value={dosisObat}
                onChange={(e) => setDosisObat(e.target.value)}
              />
              <input
                type="number"
                min={0}
                className="form-control"
                placeholder="Racik"
                title="Biaya Racik (Rp)"
                value={biayaRacik}
                onChange={(e) => setBiayaRacik(e.target.value)}
              />
              <button
                type="button"
                className="btn btn-outline"
                aria-label="Tambah Resep Obat"
                title="Tambah ke Resep"
                onClick={addResepItem}
              >
                <Plus size={15} />
              </button>
            </div>

            {resepItems.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {resepItems.map((r, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      borderRadius: 8,
                      background: 'var(--bg-surface-alt)',
                      fontSize: 13,
                    }}
                  >
                    <span>
                      <strong>{r.nama_obat}</strong> x{r.jumlah_beli} • {r.dosis} •{' '}
                      {formatRupiah(r.harga_satuan * r.jumlah_beli + r.biaya_racik)}
                    </span>
                    <button
                      type="button"
                      className="btn btn-outline btn-sm"
                      onClick={() => setResepItems(resepItems.filter((_, i) => i !== idx))}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
            <button
              type="submit"
              className="btn btn-success"
              style={{ flex: 1 }}
              disabled={submitting || !activeAntrean}
            >
              <CheckCircle size={16} />
              {submitting ? 'Menyimpan...' : 'Simpan & Rujuk Farmasi / Kasir'}
            </button>
            <button type="button" className="btn btn-outline" onClick={resetForm}>
              <RotateCcw size={15} />
              Reset Formulir
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
