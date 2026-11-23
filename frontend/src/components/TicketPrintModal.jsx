import React from 'react';
import { Printer, X } from 'lucide-react';
import { formatWaktu } from '../utils/formatters';

export default function TicketPrintModal({ ticket, onClose }) {
  if (!ticket) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: 400 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="card-header no-print">
          <h3 className="card-title">Tiket Antrean Pasien</h3>
          <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={15} />
          </button>
        </div>

        <div className="card-body printable-area" style={{ textAlign: 'center' }}>
          <div style={{ borderBottom: '2px dashed var(--border-color)', paddingBottom: 14, marginBottom: 16 }}>
            <div style={{ fontWeight: 800, fontSize: 16, letterSpacing: '0.04em' }}>
              MEDIKACARE
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
              Klinik Pratama Sehat — Tiket Antrean Resmi
            </div>
          </div>

          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            {ticket.poli_tujuan}
          </div>
          <div
            className="mono"
            style={{
              fontSize: 44,
              fontWeight: 800,
              color: 'var(--primary)',
              margin: '8px 0',
              letterSpacing: '0.03em',
            }}
          >
            {ticket.nomor_antrean}
          </div>
          <span className="badge badge-primary" style={{ marginBottom: 14 }}>
            Prioritas: {ticket.prioritas}
          </span>

          <div
            style={{
              textAlign: 'left',
              background: 'var(--bg-surface-alt)',
              padding: 12,
              borderRadius: 10,
              fontSize: 13,
              lineHeight: 1.7,
              marginTop: 10,
            }}
          >
            <div>
              <strong>Nama Pasien:</strong> {ticket.pasien_nama}
            </div>
            <div>
              <strong>No. RM:</strong> <span className="mono">{ticket.pasien_nomor_rm}</span>
            </div>
            <div>
              <strong>Waktu Daftar:</strong> {formatWaktu(ticket.waktu_daftar)}
            </div>
            <div>
              <strong>Status:</strong> {ticket.status}
            </div>
          </div>

          <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 14 }}>
            Silakan menunggu di ruang tunggu hingga nomor antrean Anda dipanggil.
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
            Cetak Tiket
          </button>
        </div>
      </div>
    </div>
  );
}
