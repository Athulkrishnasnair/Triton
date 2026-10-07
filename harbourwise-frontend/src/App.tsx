import { useCallback, useEffect, useState } from 'react';
import OceanHeader from '@/components/OceanHeader';
import Sidebar from '@/components/Sidebar';
import DashboardContent from '@/components/DashboardContent';
import { getHarbours, getHealth, loadDashboardSnapshot } from '@/services/harbourApi';
import type { AlertItem, DashboardSnapshot, HarbourRecord } from '@/data/dashboard';

function App() {
  const [harbour, setHarbour] = useState('All Harbours');
  const [harbours, setHarbours] = useState<HarbourRecord[]>([]);
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [activeNav, setActiveNav] = useState('overview');
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mq.matches);
    const handler = () => setReducedMotion(mq.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const refresh = useCallback(() => setRetry((value) => value + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    (async () => {
      try {
        await getHealth(controller.signal);
        const records = await getHarbours(controller.signal);
        setHarbours(records);
        const selected = harbour !== 'All Harbours' && !records.some((item) => item.name === harbour)
          ? 'All Harbours'
          : harbour;
        if (selected !== harbour) setHarbour(selected);
        const data = await loadDashboardSnapshot(records, selected, controller.signal);
        setSnapshot(data);
        setAlerts(data.alerts);
      } catch (cause) {
        if (cause instanceof DOMException && cause.name === 'AbortError') return;
        setError(cause instanceof Error ? cause.message : 'Unable to load harbour data.');
        setSnapshot(null);
        setAlerts([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [harbour, retry]);

  return (
    <div className="min-h-screen bg-paper font-sans antialiased">
      <OceanHeader harbour={harbour} setHarbour={setHarbour} harbours={['All Harbours', ...harbours.map((item) => item.name)]} alerts={alerts} />
      <div className="flex">
        <Sidebar active={activeNav} setActive={setActiveNav} alertCount={alerts.filter((item) => item.level !== 'info').length} connected={!error && !loading} />
        <DashboardContent harbour={harbour} reducedMotion={reducedMotion} snapshot={snapshot} loading={loading} error={error} onRetry={refresh} />
      </div>
    </div>
  );
}

export default App;
