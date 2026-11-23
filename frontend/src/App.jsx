import React, { useCallback, useEffect, useState } from 'react';
import Layout from './components/Layout';
import ReceiptPrintModal from './components/ReceiptPrintModal';
import TicketPrintModal from './components/TicketPrintModal';
import AntreanPage from './pages/AntreanPage';
import DashboardPage from './pages/DashboardPage';
import FarmasiPage from './pages/FarmasiPage';
import KasirPage from './pages/KasirPage';
import LaporanPage from './pages/LaporanPage';
import LoginPage from './pages/LoginPage';
import PasienPage from './pages/PasienPage';
import PatientPortalPage from './pages/PatientPortalPage';
import PemeriksaanPage from './pages/PemeriksaanPage';
import { api } from './services/api';

const PAGE_TITLES = {
  dashboard: 'DASHBOARD OPERASIONAL MEDIKACARE',
  pasien: 'PENDAFTARAN & DATA PASIEN',
  antrean: 'MANAJEMEN ANTREAN POLI',
  pemeriksaan: 'RUANG PERIKSA DOKTER & REKAM MEDIS',
  farmasi: 'FARMASI & INVENTARIS OBAT',
  kasir: 'KASIR & PEMBAYARAN POLIMORFIK',
  laporan: 'LAPORAN KUNJUNGAN & PENDAPATAN',
};

export default function App() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem('medikacare_theme') || 'light'
  );
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('medikacare_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [activePage, setActivePage] = useState('dashboard');
  const [guestView, setGuestView] = useState(() =>
    window.location.hash === '#/antrean-mandiri' ? 'patient-portal' : 'login'
  );

  const [summary, setSummary] = useState(null);
  const [pasienList, setPasienList] = useState([]);
  const [antreanList, setAntreanList] = useState([]);
  const [obatList, setObatList] = useState([]);
  const [resepList, setResepList] = useState([]);
  const [tagihanList, setTagihanList] = useState([]);

  const [busyAction, setBusyAction] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [printTicket, setPrintTicket] = useState(null);
  const [printReceipt, setPrintReceipt] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('medikacare_theme', theme);
  }, [theme]);

  const notify = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('medikacare_token');
    localStorage.removeItem('medikacare_user');
    setUser(null);
    setActivePage('dashboard');
  }, []);

  const loadAllData = useCallback(async () => {
    if (!localStorage.getItem('medikacare_token')) return;
    try {
      const [sum, pas, ant, obt, rsp, tag] = await Promise.all([
        api.getRingkasan(),
        api.listPasien('', true),
        api.listAntrean(),
        api.listObat(),
        api.listResepFarmasi(),
        api.listTagihan(),
      ]);
      setSummary(sum);
      setPasienList(pas);
      setAntreanList(ant);
      setObatList(obt);
      setResepList(rsp);
      setTagihanList(tag);
    } catch (err) {
      if (err.status === 401) {
        handleLogout();
      } else {
        notify(err.message || 'Gagal memuat data klinik.', 'error');
      }
    }
  }, [handleLogout, notify]);

  useEffect(() => {
    if (!user) return;
    loadAllData();

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/updates`;
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = () => {
        loadAllData();
      };
    } catch {
      // Fallback polling remains available
    }

    const poll = setInterval(loadAllData, 15000);
    return () => {
      clearInterval(poll);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [user, loadAllData]);

  const handleLoginSuccess = (token, userData) => {
    localStorage.setItem('medikacare_token', token);
    localStorage.setItem('medikacare_user', JSON.stringify(userData));
    setUser(userData);
    setActivePage('dashboard');
    notify(`Selamat datang, ${userData.nama_lengkap}`, 'success');
  };

  const handlePanggilBerikutnya = async (poli = '') => {
    setBusyAction(true);
    try {
      const called = await api.panggilAntrean(poli);
      notify(
        `Memanggil antrean ${called.nomor_antrean} — ${called.pasien_nama} (${called.poli_tujuan}).`,
        'success'
      );
      await loadAllData();
      setActivePage('pemeriksaan');
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusyAction(false);
    }
  };

  const toggleTheme = () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));

  if (!user) {
    return (
      <>
        {guestView === 'patient-portal' ? (
          <PatientPortalPage
            onBackToLogin={() => {
              window.location.hash = '';
              setGuestView('login');
            }}
            onPrintTicket={setPrintTicket}
            onNotify={notify}
            theme={theme}
            onToggleTheme={toggleTheme}
          />
        ) : (
          <LoginPage
            onLoginSuccess={handleLoginSuccess}
            onOpenPatientPortal={() => {
              window.location.hash = '#/antrean-mandiri';
              setGuestView('patient-portal');
            }}
            theme={theme}
            onToggleTheme={toggleTheme}
          />
        )}
        <TicketPrintModal ticket={printTicket} onClose={() => setPrintTicket(null)} />
        <div className="toast-container no-print">
          {toasts.map((t) => (
            <div key={t.id} className={`toast ${t.type}`}>
              <span>{t.message}</span>
            </div>
          ))}
        </div>
      </>
    );
  }

  const badges = {
    antrean: antreanList.filter((a) => a.status === 'Menunggu').length,
    farmasi: resepList.filter((r) => r.status_resep === 'Menunggu Validasi').length,
    kasir: tagihanList.filter((t) => !t.status_lunas).length,
  };

  return (
    <>
      <Layout
        user={user}
        activePage={activePage}
        onNavigate={setActivePage}
        onLogout={handleLogout}
        theme={theme}
        onToggleTheme={toggleTheme}
        badges={badges}
        pageTitle={PAGE_TITLES[activePage] || 'MEDIKACARE'}
      >
        {activePage === 'dashboard' && (
          <DashboardPage
            user={user}
            summary={summary}
            antreanList={antreanList}
            resepList={resepList}
            tagihanList={tagihanList}
            onNavigate={setActivePage}
            onPanggilBerikutnya={handlePanggilBerikutnya}
            busyAction={busyAction}
          />
        )}

        {activePage === 'pasien' && (
          <PasienPage
            pasienList={pasienList}
            onRefresh={loadAllData}
            onNotify={notify}
            onPrintTicket={setPrintTicket}
          />
        )}

        {activePage === 'antrean' && (
          <AntreanPage
            user={user}
            antreanList={antreanList}
            pasienList={pasienList}
            onRefresh={loadAllData}
            onNotify={notify}
            onPrintTicket={setPrintTicket}
            onPanggilBerikutnya={handlePanggilBerikutnya}
            busyAction={busyAction}
          />
        )}

        {activePage === 'pemeriksaan' && (
          <PemeriksaanPage
            user={user}
            antreanList={antreanList}
            obatList={obatList}
            onRefresh={loadAllData}
            onNotify={notify}
            onPanggilBerikutnya={handlePanggilBerikutnya}
            busyAction={busyAction}
          />
        )}

        {activePage === 'farmasi' && (
          <FarmasiPage
            resepList={resepList}
            obatList={obatList}
            onRefresh={loadAllData}
            onNotify={notify}
          />
        )}

        {activePage === 'kasir' && (
          <KasirPage
            tagihanList={tagihanList}
            onRefresh={loadAllData}
            onNotify={notify}
            onPrintReceipt={setPrintReceipt}
          />
        )}

        {activePage === 'laporan' && (
          <LaporanPage
            summary={summary}
            onSummaryUpdate={setSummary}
            onNotify={notify}
          />
        )}
      </Layout>

      <TicketPrintModal ticket={printTicket} onClose={() => setPrintTicket(null)} />
      <ReceiptPrintModal receipt={printReceipt} onClose={() => setPrintReceipt(null)} />

      <div className="toast-container no-print">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.type}`}>
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </>
  );
}
