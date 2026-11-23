import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  CreditCard,
  Printer,
  Receipt,
} from 'lucide-react';
import { api } from '../services/api';
import { formatRupiah, formatWaktu } from '../utils/formatters';

export default function KasirPage({
  tagihanList,
  onRefresh,
  onNotify,
  onPrintReceipt,
}) {
  const [selectedId, setSelectedId] = useState('');
  const [metode, setMetode] = useState('Tunai');
  const [nominalBayar, setNominalBayar] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const selected =
    tagihanList.find((t) => t.id_transaksi === selectedId) ||
    tagihanList.find((t) => !t.status_lunas) ||
    tagihanList[0];

  useEffect(() => {
    if (selected && !selected.status_lunas) {
      setNominalBayar(String(selected.grand_total));
    }
  }, [selected?.id_transaksi]);

  const nominalNum = Number(nominalBayar || 0);
  const kembalian = selected ? nominalNum - selected.grand_total : 0;
  const kurangBayar = selected && !selected.status_lunas && nominalNum < selected.grand_total;

  const handlePay = async (e) => {
    e.preventDefault();
    if (!selected) return;
    if (nominalNum < selected.grand_total) {
      onNotify(
        `Nominal bayar kurang dari Grand Total (${formatRupiah(selected.grand_total)}).`,
        'error'
      );
      return;
    }
    setSubmitting(true);
    try {
      const struk = await api.bayarTagihan(selected.id_transaksi, {
        nominal_bayar: nominalNum,
        metode_pembayaran: metode,
      });
      onNotify(
        `Pembayaran ${selected.id_transaksi} berhasil (Lunas). Kembalian: ${formatRupiah(struk.kembalian)}.`,
        'success'
      );
      await onRefresh();
      onPrintReceipt(struk);
    } catch (err) {
      onNotify(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid-split">
      {/* Daftar Tagihan Pasien */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Receipt size={17} color="var(--primary)" />
            Daftar Tagihan Layanan ({tagihanList.length})
          </h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID Transaksi</th>
                <th>Pasien</th>
                <th>Total Tagihan</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tagihanList.map((t) => {
                const isSelected = selected?.id_transaksi === t.id_transaksi;
                return (
                  <tr
                    key={t.id_transaksi}
                    onClick={() => setSelectedId(t.id_transaksi)}
                    style={{
                      cursor: 'pointer',
                      backgroundColor: isSelected ? 'var(--primary-soft)' : undefined,
                    }}
                  >
                    <td>
                      <div className="mono" style={{ fontWeight: 700, fontSize: 12.5 }}>
                        {t.id_transaksi}
                      </div>
                      <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                        {formatWaktu(t.waktu)}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{t.pasien_nama}</div>
                      <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                        {t.pasien_nomor_rm} • Resep: {t.status_resep}
                      </div>
                    </td>
                    <td style={{ fontWeight: 700 }}>{formatRupiah(t.grand_total)}</td>
                    <td>
                      <span className={`badge ${t.status_lunas ? 'badge-success' : 'badge-warning'}`}>
                        {t.status_lunas ? 'Lunas' : 'Belum Bayar'}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {tagihanList.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                    Belum ada data tagihan.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rincian Tagihan Polimorfik & Pembayaran */}
      <div className="card" style={{ alignSelf: 'start' }}>
        <div className="card-header">
          <h3 className="card-title">
            <CreditCard size={17} color="var(--success)" />
            Verifikasi Tagihan & Pembayaran
          </h3>
          {selected && (
            <span className="mono" style={{ fontSize: 12.5, fontWeight: 700 }}>
              {selected.id_transaksi}
            </span>
          )}
        </div>

        {!selected ? (
          <div className="card-body" style={{ color: 'var(--text-muted)' }}>
            Pilih transaksi pada daftar di sebelah kiri untuk memproses pembayaran.
          </div>
        ) : (
          <div className="card-body">
            <div
              style={{
                padding: 12,
                borderRadius: 10,
                background: 'var(--bg-surface-alt)',
                marginBottom: 14,
                fontSize: 13,
                display: 'flex',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 8,
              }}
            >
              <div>
                <strong>Pasien:</strong> {selected.pasien_nama} ({selected.pasien_nomor_rm})
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  Diagnosis: {selected.diagnosis || '-'}
                </div>
              </div>
              <span
                className={`badge ${
                  selected.status_resep === 'Divalidasi' ? 'badge-success' : 'badge-warning'
                }`}
              >
                Status Resep: {selected.status_resep}
              </span>
            </div>

            {selected.status_resep === 'Menunggu Validasi' && !selected.status_lunas && (
              <div className="alert alert-warning" style={{ marginBottom: 14 }}>
                <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
                <span>
                  Catatan: Resep pasien ini belum divalidasi oleh Petugas Farmasi. Pastikan obat telah disiapkan sebelum menyelesaikan transaksi.
                </span>
              </div>
            )}

            <div className="table-wrap" style={{ marginBottom: 16 }}>
              <table>
                <thead>
                  <tr>
                    <th>Komponen Layanan</th>
                    <th>Kelas PBO</th>
                    <th style={{ textAlign: 'right' }}>Biaya</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.rincian_layanan.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{item.nama_layanan}</div>
                        <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                          Dasar: {formatRupiah(item.tarif_dasar)}
                          {item.jumlah > 1 ? ` × ${item.jumlah}` : ''}
                          {item.biaya_tambahan > 0
                            ? ` + Tambahan: ${formatRupiah(item.biaya_tambahan)}`
                            : ''}
                        </div>
                      </td>
                      <td>
                        <span className="badge badge-primary">{item.tipe_layanan}</span>
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 700 }}>
                        {formatRupiah(item.total_biaya)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div
              style={{
                padding: 14,
                borderRadius: 10,
                background: 'var(--bg-surface-alt)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 16,
              }}
            >
              <span style={{ fontWeight: 700, fontSize: 15 }}>Grand Total Tagihan</span>
              <span style={{ fontWeight: 800, fontSize: 22, color: 'var(--primary)' }}>
                {formatRupiah(selected.grand_total)}
              </span>
            </div>

            {selected.status_lunas ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="alert alert-success">
                  <CheckCircle2 size={16} />
                  <span>
                    Transaksi <strong>LUNAS</strong> ({selected.metode_pembayaran}) • Dibayar:{' '}
                    {formatRupiah(selected.nominal_bayar)} • Kembalian:{' '}
                    {formatRupiah(selected.kembalian)}
                  </span>
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => onPrintReceipt(selected)}
                >
                  <Printer size={15} />
                  Cetak Ulang Struk Faktur
                </button>
              </div>
            ) : (
              <form onSubmit={handlePay} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">Metode Pembayaran</label>
                    <select
                      className="form-control"
                      value={metode}
                      onChange={(e) => {
                        setMetode(e.target.value);
                        if (e.target.value === 'Nontunai') {
                          setNominalBayar(String(selected.grand_total));
                        }
                      }}
                    >
                      <option value="Tunai">Tunai</option>
                      <option value="Nontunai">Nontunai (QRIS / Debit)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Nominal Uang Dibayarkan (Rp)</label>
                    <input
                      type="number"
                      min={0}
                      className="form-control mono"
                      value={nominalBayar}
                      onChange={(e) => setNominalBayar(e.target.value)}
                      required
                    />
                  </div>
                </div>

                {kurangBayar ? (
                  <div className="alert alert-danger">
                    <AlertCircle size={16} />
                    <span>
                      Nominal pembayaran kurang {formatRupiah(selected.grand_total - nominalNum)} dari grand total.
                    </span>
                  </div>
                ) : (
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      borderRadius: 9,
                      background: 'var(--success-soft)',
                      color: 'var(--success)',
                      fontWeight: 700,
                    }}
                  >
                    <span>Uang Kembalian Otomatis:</span>
                    <span>{formatRupiah(Math.max(0, kembalian))}</span>
                  </div>
                )}

                <button
                  type="submit"
                  className="btn btn-success"
                  disabled={submitting || kurangBayar}
                >
                  <CheckCircle2 size={16} />
                  {submitting ? 'Memproses Pembayaran...' : 'Proses Pembayaran & Cetak Faktur'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
