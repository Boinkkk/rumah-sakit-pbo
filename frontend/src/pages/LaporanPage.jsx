import React, { useState } from 'react';
import {
  AlertTriangle,
  BarChart3,
  Calendar,
  Download,
  RefreshCw,
} from 'lucide-react';
import StatCards from '../components/StatCards';
import { api } from '../services/api';
import { formatRupiah, formatTanggalIndo } from '../utils/formatters';

export default function LaporanPage({ summary, onSummaryUpdate, onNotify }) {
  const todayStr = new Date().toISOString().slice(0, 10);
  const weekAgo = new Date(Date.now() - 6 * 86400000).toISOString().slice(0, 10);

  const [mulai, setMulai] = useState(weekAgo);
  const [akhir, setAkhir] = useState(todayStr);
  const [loading, setLoading] = useState(false);

  const handleFilter = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.getRingkasan(mulai, akhir);
      onSummaryUpdate(res);
      onNotify('Laporan operasional diperbarui.', 'success');
    } catch (err) {
      onNotify(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const exportCsv = () => {
    const rows = summary?.grafik_harian || [];
    const header = 'Tanggal,Jumlah Kunjungan,Pendapatan (IDR)\n';
    const body = rows
      .map((r) => `${r.tanggal},${r.kunjungan},${r.pendapatan}`)
      .join('\n');
    const blob = new Blob([header + body], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `laporan-medikacare-${mulai}-sd-${akhir}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const daily = summary?.grafik_harian || [];
  const maxPendapatan = Math.max(1, ...daily.map((d) => d.pendapatan));
  const poliCounts = summary?.distribusi_poli || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      <StatCards summary={summary} />

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Calendar size={17} color="var(--primary)" />
            Filter Periode Laporan & Rekapitulasi
          </h3>

          <form onSubmit={handleFilter} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type="date"
              className="form-control"
              style={{ width: 155 }}
              value={mulai}
              onChange={(e) => setMulai(e.target.value)}
            />
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>s/d</span>
            <input
              type="date"
              className="form-control"
              style={{ width: 155 }}
              value={akhir}
              onChange={(e) => setAkhir(e.target.value)}
            />
            <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>
              <RefreshCw size={14} />
              Terapkan
            </button>
            <button type="button" className="btn btn-outline btn-sm" onClick={exportCsv}>
              <Download size={14} />
              Ekspor CSV
            </button>
          </form>
        </div>

        <div className="card-body">
          <div className="grid-2" style={{ marginBottom: 18 }}>
            <div
              style={{
                padding: 16,
                borderRadius: 12,
                background: 'var(--bg-surface-alt)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                Total Pendapatan Periode Terpilih ({summary?.total_transaksi_lunas || 0} Transaksi Lunas)
              </div>
              <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--success)', marginTop: 4 }}>
                {formatRupiah(summary?.total_pendapatan_periode || 0)}
              </div>
            </div>

            <div
              style={{
                padding: 16,
                borderRadius: 12,
                background: 'var(--bg-surface-alt)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginBottom: 6 }}>
                Distribusi Kunjungan Poli Hari Ini
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {Object.entries(poliCounts).map(([poli, count]) => (
                  <span key={poli} className="badge badge-primary" style={{ fontSize: 12.5, padding: '6px 11px' }}>
                    {poli}: {count} Pasien
                  </span>
                ))}
              </div>
            </div>
          </div>

          <h4 style={{ margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
            <BarChart3 size={16} color="var(--primary)" />
            Grafik Pendapatan & Kunjungan Harian
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {daily.map((row) => {
              const pct = Math.round((row.pendapatan / maxPendapatan) * 100);
              return (
                <div
                  key={row.tanggal}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '170px 1fr 120px 140px',
                    alignItems: 'center',
                    gap: 12,
                    fontSize: 13,
                  }}
                >
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                    {formatTanggalIndo(row.tanggal)}
                  </span>
                  <div
                    style={{
                      height: 12,
                      borderRadius: 999,
                      background: 'var(--bg-surface-alt)',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.max(pct, row.pendapatan > 0 ? 4 : 0)}%`,
                        height: '100%',
                        background: 'var(--primary)',
                        borderRadius: 999,
                      }}
                    />
                  </div>
                  <span className="badge badge-muted" style={{ justifySelf: 'start' }}>
                    {row.kunjungan} Kunjungan
                  </span>
                  <span style={{ textAlign: 'right', fontWeight: 700 }}>
                    {formatRupiah(row.pendapatan)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Peringatan Stok Obat Menipis */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <AlertTriangle size={17} color="var(--warning)" />
            Peringatan Stok Obat Menipis (≤ 20)
          </h3>
        </div>
        <div className="card-body">
          {(summary?.stok_menipis || []).length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13.5 }}>
              Seluruh stok obat berada di atas batas minimum aman.
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {summary.stok_menipis.map((o) => (
                <span key={o.kode_obat} className="badge badge-danger" style={{ padding: '7px 12px', fontSize: 12.5 }}>
                  {o.kode_obat} — {o.nama_obat} (Sisa: {o.stok})
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
