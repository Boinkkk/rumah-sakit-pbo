import React from 'react';
import { Clock, Stethoscope, Users, Wallet } from 'lucide-react';
import { formatRupiah } from '../utils/formatters';

export default function StatCards({ summary }) {
  const s = summary || {
    pasien_hari_ini: 0,
    antrean_menunggu: 0,
    sedang_diperiksa: '-',
    total_pendapatan_hari_ini: 0,
  };

  return (
    <div className="kpi-grid">
      <div className="kpi-card primary">
        <div className="kpi-label">
          <span>Pasien Hari Ini</span>
          <Users size={16} />
        </div>
        <div className="kpi-value">{s.pasien_hari_ini} Orang</div>
      </div>

      <div className="kpi-card warning">
        <div className="kpi-label">
          <span>Antrean Menunggu</span>
          <Clock size={16} />
        </div>
        <div className="kpi-value">{s.antrean_menunggu} Pasien</div>
      </div>

      <div className="kpi-card teal">
        <div className="kpi-label">
          <span>Sedang Diperiksa</span>
          <Stethoscope size={16} />
        </div>
        <div className="kpi-value mono">
          {s.sedang_diperiksa && s.sedang_diperiksa !== '-'
            ? `Nomor ${s.sedang_diperiksa}`
            : '-'}
        </div>
      </div>

      <div className="kpi-card success">
        <div className="kpi-label">
          <span>Total Pendapatan Hari Ini</span>
          <Wallet size={16} />
        </div>
        <div className="kpi-value">{formatRupiah(s.total_pendapatan_hari_ini)}</div>
      </div>
    </div>
  );
}
