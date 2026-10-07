import { Download, Calendar, Info, AlertTriangle, XCircle, Clock, RefreshCw } from 'lucide-react';
import type { AlertItem, DashboardSnapshot } from '@/data/dashboard';
import StatStrip from '@/components/StatStrip';

function SectionTitle({ children, sub }: { children: React.ReactNode; sub?: string }) {
  return (
    <div className="mb-5">
      <h2 className="font-display font-semibold text-[15px] text-navy-900 tracking-tight">{children}</h2>
      {sub && <p className="text-[11px] text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function DashboardContent({ harbour, reducedMotion, snapshot, loading, error, onRetry }: {
  harbour: string;
  reducedMotion: boolean;
  snapshot: DashboardSnapshot | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  const markets = snapshot?.markets ?? [];
  const filteredVessels = snapshot?.vessels ?? [];
  const filteredLandings = snapshot?.landings ?? [];
  const facilities = snapshot?.facilities ?? [];
  const buyers = snapshot?.buyers ?? [];
  const announcements = snapshot?.announcements ?? [];
  const alerts = snapshot?.alerts ?? [];
  const stats = snapshot?.stats ?? [];
  const conditions = snapshot?.conditions ?? [];
  const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });
  const empty = (label: string, columns = 5) => <tr><td colSpan={columns} className="py-5 text-center text-sm text-slate-500">{label}</td></tr>;
  const landingTime = (value: string | null) => {
    if (!value) return 'Time unavailable';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? 'Time unavailable' : new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit',
    }).format(date);
  };
  const alertIcons: Record<AlertItem['level'], { icon: typeof Info; color: string }> = {
    info: { icon: Info, color: 'text-ocean-400' },
    warning: { icon: AlertTriangle, color: 'text-amber-500' },
    critical: { icon: XCircle, color: 'text-red-500' },
  };

  if (error) return <main className="flex-1 min-w-0 bg-paper px-5 sm:px-8 py-10"><div className="max-w-xl border-t border-slate-200 pt-6"><h1 className="font-display text-2xl font-semibold text-navy-900">Harbour data is unavailable</h1><p className="mt-2 text-sm text-slate-600">{error}</p><button onClick={onRetry} className="mt-5 inline-flex min-h-11 items-center gap-2 bg-navy-800 px-4 py-2 text-sm text-white"><RefreshCw className="h-4 w-4" />Retry connection</button></div></main>;

  return (
    <main className="flex-1 min-w-0 bg-paper">
      {/* Editorial page header */}
      <div className="px-5 sm:px-8 xl:px-10 pt-7 sm:pt-9 pb-6">
        <div className="flex items-end justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-[30px] sm:text-[34px] font-display font-semibold text-navy-900 tracking-[-0.02em] leading-tight">
              Harbour overview
            </h1>
            <p className="text-sm text-slate-600 mt-2">
              Prices, buyer demand and landing records · <span className="text-navy-700 font-medium">{harbour}</span>
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button className="flex min-h-11 items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-navy-900 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export
            </button>
            <button className="flex min-h-11 items-center gap-1.5 text-sm font-medium text-white bg-navy-800 px-4 py-2 hover:bg-navy-700 transition-colors">
              <Calendar className="w-3.5 h-3.5" /> Schedule Report
            </button>
          </div>
        </div>
      </div>

      {snapshot?.isDemo && <div className="mx-5 sm:mx-8 xl:mx-10 mt-2 border-y border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">The backend marks some returned records as demonstration data.</div>}
      {loading && <div className="mx-5 sm:mx-8 xl:mx-10 mt-4 text-sm text-slate-600" role="status">Loading harbour data…</div>}

      {/* Thin divider */}
      <div className="mx-5 sm:mx-8 xl:mx-10 border-t border-slate-200/70" />

      {/* Statistics strip — no cards, just typography + thin separators */}
      <div className="px-5 sm:px-8 xl:px-10 py-5">
        <StatStrip stats={stats} reducedMotion={reducedMotion} />
      </div>

      <div className="mx-5 sm:mx-8 xl:mx-10 border-t border-slate-200/70" />

      {/* Main content area: asymmetric grid */}
      <div className="px-5 sm:px-8 xl:px-10 py-7 space-y-8">
        {/* Row 1: Market Prices (large, left) + Harbour Conditions (smaller, right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 xl:gap-10">
          {/* Market Prices — the dominant section */}
          <div className="lg:col-span-8">
            <SectionTitle sub="Latest prices reported by the backend">Market Prices</SectionTitle>
            <div className="overflow-x-auto scroll-thin">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 pr-4">Species</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4">₹/kg</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4">Change</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4 hidden sm:table-cell">Range</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 pl-4">Demand</th>
                  </tr>
                </thead>
                <tbody>
                  {markets.length === 0 ? empty(loading ? 'Loading prices…' : 'No market prices returned by the backend.') : markets.map((m) => (
                    <tr key={`${m.id}-${m.harbour}`} className="border-b border-slate-100 hover:bg-white/40 transition-colors">
                      <td className="py-3.5 pr-4">
                        <div className="text-sm font-medium text-navy-900">{m.species}</div>
                        <div className="text-xs text-slate-600 mt-0.5">{m.harbour}</div>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <span className="text-[15px] font-display font-semibold text-navy-900 font-mono">{currency.format(m.pricePerKg)}</span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <span className="text-xs text-slate-600" title="Historical comparison is not provided by the backend">No history</span>
                      </td>
                      <td className="py-3.5 px-4 text-right text-[12px] font-mono text-slate-500 hidden sm:table-cell">
                        {currency.format(m.minPrice)}–{currency.format(m.maxPrice)}
                      </td>
                      <td className="py-3.5 pl-4 text-right">
                        <span className="inline-flex items-center gap-1.5 text-xs text-slate-700 justify-end">
                          <span className={`w-1.5 h-1.5 rounded-full ${m.demandKg ? 'bg-teal-400' : 'bg-slate-300'}`} />
                          {m.demandKg === null ? 'No record' : `${m.demandKg.toLocaleString('en-IN')} kg open`}
                        </span>
                        <div className="mt-1 text-right text-[11px] text-slate-500">{m.freshness.toLowerCase()} price{m.isDemo ? ' · demo data' : ''}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Harbour Conditions — smaller, right side */}
          <div className="lg:col-span-4">
            <SectionTitle>Harbour Conditions</SectionTitle>
            <div className="space-y-5">
              {conditions.map((c) => <ConditionRow key={c.label} label={c.label} value={c.value} detail={c.detail} dot={c.status === 'available' ? 'bg-teal-400' : c.status === 'limited' ? 'bg-amber-400' : 'bg-slate-300'} />)}
            </div>
          </div>
        </div>

        {/* Thin separator */}
        <div className="border-t border-slate-200/70" />

        {/* Row 2: Vessel Activity + Facilities + Active Buyers */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 xl:gap-10">
          {/* Vessel Activity — large */}
          <div className="lg:col-span-7">
            <SectionTitle sub="Vessel tracking is not available from the current backend API">Vessel Activity</SectionTitle>
            <div className="overflow-x-auto scroll-thin">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 pr-4">Vessel</th>
                    <th className="text-left text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4 hidden sm:table-cell">Harbour</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4">Arrival</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4">Catch</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 pl-4">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVessels.length === 0 ? empty('No vessel tracking endpoint is available.') : filteredVessels.map((v) => (
                    <tr key={v.id} className="border-b border-slate-100 hover:bg-white/40 transition-colors">
                      <td className="py-3 pr-4">
                        <div className="text-[13px] font-medium text-navy-900">{v.name}</div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">{v.id} · {v.type}</div>
                      </td>
                      <td className="py-3 px-4 text-[12px] text-slate-500 hidden sm:table-cell">{v.harbour}</td>
                      <td className="py-3 px-4 text-right text-[12px] font-mono text-slate-600">{v.arrival}</td>
                      <td className="py-3 px-4 text-right">
                        <div className="text-[13px] font-medium text-navy-900 font-mono">{v.catchKg.toLocaleString()} kg</div>
                        <div className="text-[10px] text-slate-500">{v.value}</div>
                      </td>
                      <td className="py-3 pl-4 text-right">
                        <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-600 justify-end">
                          <span className={`w-1.5 h-1.5 rounded-full ${v.status === 'Returning' ? 'bg-amber-400' : v.status === 'At Sea' ? 'bg-ocean-400' : v.status === 'Docked' ? 'bg-teal-400' : 'bg-slate-400'}`} />
                          {v.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Facilities + Buyers — stacked, narrower */}
          <div className="lg:col-span-5 space-y-10">
            {/* Facilities */}
            <div>
              <SectionTitle>Facilities</SectionTitle>
              <div className="space-y-px">
                {facilities.length === 0 ? <div className="py-4 text-[12px] text-slate-500">No facility status returned by the backend.</div> : facilities.map((f) => (
                  <div key={`${f.name}-${f.harbour}`} className="flex items-center justify-between py-3 border-b border-slate-100">
                    <span className="text-[13px] text-slate-700 font-medium">{f.name}<span className="ml-2 text-[10px] text-slate-500">{f.harbour}</span></span>
                    <span className="inline-flex items-center gap-2 text-[11px] text-slate-500">
                      <span className={`w-1.5 h-1.5 rounded-full ${f.status.toLowerCase() === 'limited' ? 'bg-amber-400' : f.status.toLowerCase() === 'available' ? 'bg-teal-400' : 'bg-slate-300'}`} />
                      {f.status}{f.available !== null && f.capacity !== null ? ` · ${f.available}/${f.capacity} ${f.unit}` : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Active Buyers */}
            <div>
              <SectionTitle>Active Buyers</SectionTitle>
              <div className="space-y-px">
                {buyers.length === 0 ? <div className="py-4 text-[12px] text-slate-500">No active buyers returned by the backend.</div> : buyers.map((b) => (
                  <div key={b.id} className="flex items-center justify-between py-3 border-b border-slate-100">
                    <span className="text-[13px] text-slate-700 font-medium">{b.name}{b.organization && <span className="ml-2 text-[10px] text-slate-500">{b.organization}</span>}</span>
                    <span className="inline-flex items-center gap-2 text-[11px] text-slate-500">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
                      {b.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Thin separator */}
        <div className="border-t border-slate-200/70" />

        {/* Row 3: Landings + Announcements + Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 xl:gap-10">
          {/* Landings */}
          <div className="lg:col-span-5">
            <SectionTitle sub="Landing records logged today">Today's Landings</SectionTitle>
            <div className="overflow-x-auto scroll-thin">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 pr-4">Harbour</th>
                    <th className="text-left text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4">Species</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 px-4">Vol</th>
                    <th className="text-right text-[10px] font-semibold text-slate-500 tracking-[0.12em] uppercase py-2.5 pl-4">Landed at</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLandings.length === 0 ? empty(loading ? 'Loading landings…' : 'No landings reported today.', 4) : filteredLandings.map((l) => (
                    <tr key={l.id} className="border-b border-slate-100 hover:bg-white/40 transition-colors">
                      <td className="py-3 pr-4 text-[13px] font-medium text-navy-900">{l.harbour}</td>
                      <td className="py-3 px-4 text-[12px] text-slate-600">{l.species}</td>
                      <td className="py-3 px-4 text-right text-sm font-mono text-slate-700">{l.volume.toLocaleString('en-IN')} kg</td>
                      <td className="py-3 pl-4 text-right text-xs text-slate-600">{landingTime(l.landingTime)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Announcements */}
          <div className="lg:col-span-4">
            <SectionTitle>Harbour Announcements</SectionTitle>
            <div className="space-y-px">
              {announcements.length === 0 ? <div className="py-4 text-[12px] text-slate-500">No announcements returned by the backend.</div> : announcements.map((a) => (
                <div key={a.id} className="flex items-start gap-3 py-3 border-b border-slate-100">
                  <span className="text-[11px] font-mono text-slate-500 w-10 shrink-0 pt-0.5">{a.time}</span>
                  <span className="text-[13px] text-slate-700 leading-relaxed"><span className="font-medium">{a.title}</span>{a.message && ` · ${a.message}`}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Alerts */}
          <div className="lg:col-span-3">
            <SectionTitle>Live Alerts</SectionTitle>
            <div className="space-y-px">
              {alerts.length === 0 ? <div className="py-4 text-[12px] text-slate-500">No active alerts.</div> : alerts.map((a) => {
                const { icon: Icon, color } = alertIcons[a.level];
                return (
                  <div key={a.id} className="py-3 border-b border-slate-100">
                    <div className="flex items-start gap-2.5">
                      <Icon className={`w-3.5 h-3.5 ${color} shrink-0 mt-0.5`} />
                      <div className="flex-1 min-w-0">
                        <div className="text-[12px] font-medium text-navy-900">{a.title}</div>
                        <div className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{a.detail}</div>
                        <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
                          <Clock className="w-2.5 h-2.5" /> {a.time}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-6 pb-8 text-center text-[10px] text-slate-500 tracking-wide">
          KALASTUS Fishing Harbour Network · Data supplied by the Harbour OS API
        </div>
      </div>
    </main>
  );
}

function ConditionRow({ label, value, detail, dot }: { label: string; value: string; detail: string; dot: string }) {
  return (
    <div className="flex items-baseline justify-between">
      <div>
        <div className="text-[10px] font-semibold text-slate-500 tracking-[0.14em] uppercase">{label}</div>
        <div className="text-[18px] font-display font-semibold text-navy-900 mt-1 leading-none">{value}</div>
        <div className="text-[11px] text-slate-500 mt-1">{detail}</div>
      </div>
      <span className={`w-2 h-2 rounded-full ${dot} shrink-0`} />
    </div>
  );
}
