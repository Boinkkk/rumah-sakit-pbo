import React from 'react';
import { CheckCircle2, Printer, X } from 'lucide-react';
import { formatRupiah, formatWaktu } from '../utils/formatters';

export default function ReceiptPrintModal({ receipt, onClose }) {
  if (!receipt) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="card-header no-print">
          <h3 className="card-title">
            <CheckCircle2 size={18} color="var(--success)" />
            Faktur Pembayaran Resmi
          </h3>
          <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={15} />
          </button>
        </div>

        <div className="card-body printable-area">
          <div style={{ textAlign: 'center', borderBottom: '2px dashed var(--border-color)', paddingBottom: 12, marginBottom: 14 }}>
            <div style={{ fontWeight: 800, fontSize: 17 }}>MEDIKACARE — KLINIK PRATAMA SEHAT</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Jl. Raya Telang Indah, Bangkalan • Telp. (031) 301-1146
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12.5, marginBottom: 14 }}>
            <div>
              <strong>No. Faktur:</strong> <span className="mono">{receipt.id_transaksi}</span>
            </div>
            <div>
              <strong>Waktu:</strong> {formatWaktu(receipt.waktu)}
            </div>
            <div>
              <strong>Pasien:</strong> {receipt.pasien_nama || '-'} ({receipt.pasien_nomor_rm})
            </div>
            <div>
              <strong>Metode:</strong> {receipt.metode_pembayaran} • <strong>LUNAS</strong>
            </div>
          </div>

          <table style={{ fontSize: 12.5, marginBottom: 14 }}>
            <thead>
              <tr>
                <th>Layanan / Item</th>
                <th>Tipe</th>
                <th style={{ textAlign: 'right' }}>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {(receipt.rincian_layanan || []).map((item, idx) => (
                <tr key={idx}>
                  <td>{item.deskripsi || item.nama_layanan}</td>
                  <td>
                    <span className="badge badge-muted">{item.tipe_layanan}</span>
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>
                    {formatRupiah(item.total_biaya)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div
            style={{
              background: 'var(--bg-surface-alt)',
              padding: 12,
              borderRadius: 10,
              fontSize: 13.5,
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 800, fontSize: 15 }}>
              <span>Grand Total</span>
              <span>{formatRupiah(receipt.grand_total)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Nominal Bayar ({receipt.metode_pembayaran})</span>
              <span>{formatRupiah(receipt.nominal_bayar)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--success)', fontWeight: 700 }}>
              <span>Kembalian</span>
              <span>{formatRupiah(receipt.kembalian)}</span>
            </div>
          </div>

          <div style={{ textAlign: 'center', fontSize: 11.5, color: 'var(--text-muted)', marginTop: 14 }}>
            Terima kasih atas kepercayaan Anda. Semoga lekas sembuh.
          </div>
        </div>

        <div
          className="card-header no-print"
          style={{ borderTop: '1px solid var(--border-color)', borderBottom: 'none', justifyContent: 'flex-end' }}
        >
          <button type="button" className="btn btn-outline" onClick={onClose}>
            Tutup
          </button>
          <button type="button" className="btn btn-primary" onClick={() => window.print()}>
            <Printer size={15} />
            Cetak Struk
          </button>
        </div>
      </div>
    </div>
  );
}
