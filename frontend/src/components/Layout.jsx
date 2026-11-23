import React, { useEffect, useState } from 'react';
import {
  Activity,
  ClipboardList,
  CreditCard,
  FileBarChart2,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Pill,
  Stethoscope,
  Sun,
  Users,
  X,
} from 'lucide-react';
import { ROLE_LABELS } from '../utils/formatters';

const ALL_MENU_ITEMS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    roles: ['PetugasAdministrasi', 'Dokter', 'PetugasFarmasi', 'Kasir'],
  },
  {
    id: 'pasien',
    label: 'Pendaftaran Pasien',
    icon: Users,
    roles: ['PetugasAdministrasi'],
  },
  {
    id: 'antrean',
    label: 'Antrean Poli',
    icon: ClipboardList,
    roles: ['PetugasAdministrasi', 'Dokter'],
  },
  {
    id: 'pemeriksaan',
    label: 'Pemeriksaan Dokter',
    icon: Stethoscope,
    roles: ['Dokter'],
  },
  {
    id: 'farmasi',
    label: 'Farmasi & Obat',
    icon: Pill,
    roles: ['PetugasFarmasi'],
  },
  {
    id: 'kasir',
    label: 'Kasir & Pembayaran',
    icon: CreditCard,
    roles: ['Kasir'],
  },
  {
    id: 'laporan',
    label: 'Laporan Kunjungan',
    icon: FileBarChart2,
    roles: ['PetugasAdministrasi', 'Dokter', 'PetugasFarmasi', 'Kasir'],
  },
];

export default function Layout({
  user,
  activePage,
  onNavigate,
  onLogout,
  theme,
  onToggleTheme,
  badges = {},
  pageTitle,
  children,
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [clock, setClock] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const visibleMenu = ALL_MENU_ITEMS.filter((m) => m.roles.includes(user.peran));
  const formattedClock = new Intl.DateTimeFormat('id-ID', {
    weekday: 'long',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(clock);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''} no-print`}>
        <div>
          <div className="sidebar-brand">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h1>
                <Activity size={20} color="#38bdf8" />
                MEDIKACARE
              </h1>
              <button
                type="button"
                className="btn btn-sm mobile-menu-btn"
                style={{ background: 'transparent', color: '#94a3b8', border: 'none' }}
                onClick={() => setSidebarOpen(false)}
                aria-label="Tutup menu"
              >
                <X size={18} />
              </button>
            </div>
            <p>Klinik Pratama Sehat</p>
          </div>

          <nav className="sidebar-nav" aria-label="Menu Utama">
            {visibleMenu.map((item) => {
              const Icon = item.icon;
              const badgeVal = badges[item.id];
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                  onClick={() => {
                    onNavigate(item.id);
                    setSidebarOpen(false);
                  }}
                >
                  <span className="nav-item-left">
                    <Icon size={17} />
                    <span>{item.label}</span>
                  </span>
                  {badgeVal > 0 && <span className="nav-badge">{badgeVal}</span>}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="user-card">
            <strong>{user.nama_lengkap}</strong>
            <div>Role: {ROLE_LABELS[user.peran] || user.peran}</div>
            {user.spesialisasi && <div>{user.spesialisasi}</div>}
            {user.shift_kerja && <div>Shift: {user.shift_kerja}</div>}
            {user.nomor_loket && <div>{user.nomor_loket}</div>}
          </div>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            style={{
              width: '100%',
              color: '#f8fafc',
              borderColor: 'rgba(255,255,255,0.18)',
            }}
            onClick={onLogout}
          >
            <LogOut size={14} />
            Keluar Akun
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="top-header no-print">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              type="button"
              className="btn btn-outline btn-sm mobile-menu-btn"
              onClick={() => setSidebarOpen(true)}
              aria-label="Buka menu"
            >
              <Menu size={17} />
            </button>
            <h2 className="header-title">{pageTitle}</h2>
          </div>

          <div className="header-right">
            <span
              style={{
                fontSize: 12.5,
                color: 'var(--text-muted)',
                fontWeight: 500,
              }}
            >
              {formattedClock}
            </span>
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={onToggleTheme}
              title={theme === 'dark' ? 'Beralih ke Mode Terang' : 'Beralih ke Mode Gelap'}
            >
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
              <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
            </button>
          </div>
        </header>

        <main className="content-container">{children}</main>
      </div>
    </div>
  );
}
