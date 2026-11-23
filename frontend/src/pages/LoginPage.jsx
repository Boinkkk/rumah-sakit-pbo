import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  CreditCard,
  LogIn,
  Moon,
  Pill,
  Stethoscope,
  Sun,
  UserCheck,
} from 'lucide-react';
import { api } from '../services/api';

const ROLES = [
  {
    id: 'PetugasAdministrasi',
    label: 'Resepsionis / Admin',
    demoUser: 'admin',
    icon: UserCheck,
  },
  {
    id: 'Dokter',
    label: 'Dokter Pemeriksa',
    demoUser: 'dokter',
    icon: Stethoscope,
  },
  {
    id: 'PetugasFarmasi',
    label: 'Petugas Farmasi',
    demoUser: 'farmasi',
    icon: Pill,
  },
  {
    id: 'Kasir',
    label: 'Kasir Klinik',
    demoUser: 'kasir',
    icon: CreditCard,
  },
];

export default function LoginPage({
  onLoginSuccess,
  onOpenPatientPortal,
  theme,
  onToggleTheme,
}) {
  const [selectedRole, setSelectedRole] = useState('Dokter');
  const [username, setUsername] = useState('dokter');
  const [password, setPassword] = useState('medika123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSelectRole = (role) => {
    setSelectedRole(role.id);
    setUsername(role.demoUser);
    setPassword('medika123');
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.login({
        username: username.trim(),
        password,
        peran: selectedRole,
      });
      onLoginSuccess(res.access_token, res.user);
    } catch (err) {
      setError(err.message || 'Gagal masuk ke sistem.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, color: 'var(--primary)', fontWeight: 800, fontSize: 22 }}>
              <Activity size={24} />
              MEDIKACARE
            </div>
            <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>
              Sistem Informasi Manajemen Layanan Klinik Pratama Sehat
            </p>
          </div>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={onToggleTheme}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="form-group">
            <label className="form-label">Pilih Peran Pengguna (Role-Based Access)</label>
            <div className="role-grid">
              {ROLES.map((role) => {
                const Icon = role.icon;
                const active = selectedRole === role.id;
                return (
                  <button
                    key={role.id}
                    type="button"
                    className={`role-btn ${active ? 'selected' : ''}`}
                    onClick={() => handleSelectRole(role)}
                  >
                    <Icon size={16} />
                    <span>{role.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-username">
              Nama Pengguna (Username)
            </label>
            <input
              id="login-username"
              type="text"
              className="form-control"
              placeholder="Masukkan username staf..."
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">
              Kata Sandi
            </label>
            <input
              id="login-password"
              type="password"
              className="form-control"
              placeholder="Masukkan kata sandi..."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && (
            <div className="alert alert-danger" role="alert">
              <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ padding: '11px 16px' }}>
            <LogIn size={16} />
            {loading ? 'Memverifikasi Kredensial...' : 'Masuk ke Sistem MedikaCare'}
          </button>

          <button
            type="button"
            className="btn btn-outline"
            onClick={onOpenPatientPortal}
            style={{ padding: '10px 16px', borderColor: 'var(--teal)', color: 'var(--teal)' }}
          >
            Pasien? Ambil Nomor Antrean Mandiri (Tanpa Login)
          </button>
        </form>

        <div
          style={{
            marginTop: 18,
            paddingTop: 14,
            borderTop: '1px solid var(--border-color)',
            fontSize: 12,
            color: 'var(--text-muted)',
            lineHeight: 1.6,
          }}
        >
          <strong>Akun Demo Siap Pakai</strong> (kata sandi: <code className="mono">medika123</code>):
          <div>
            Resepsionis: <code className="mono">admin</code> • Dokter Umum:{' '}
            <code className="mono">dokter</code> • Farmasi: <code className="mono">farmasi</code> • Kasir:{' '}
            <code className="mono">kasir</code>
          </div>
          <div>
            Dokter lain: <code className="mono">dokter_gigi</code>,{' '}
            <code className="mono">dokter_anak</code>
          </div>
        </div>
      </div>
    </div>
  );
}
