import {
  LayoutDashboard, Ship, Fish, BarChart3, MapPin,
  Bell, FileText, Settings, LifeBuoy,
} from 'lucide-react';

export interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const nav: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'vessels', label: 'Vessel Tracking', icon: Ship },
  { id: 'landings', label: 'Landings Log', icon: Fish },
  { id: 'market', label: 'Market Prices', icon: BarChart3 },
  { id: 'harbours', label: 'Harbour Map', icon: MapPin },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'reports', label: 'Reports', icon: FileText },
];

const bottom: NavItem[] = [
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'help', label: 'Help & Support', icon: LifeBuoy },
];

export default function Sidebar({
  active,
  setActive,
  alertCount,
  connected,
}: {
  active: string;
  setActive: (id: string) => void;
  alertCount: number;
  connected: boolean;
}) {
  return (
    <aside className="w-14 sm:w-16 md:w-52 shrink-0 bg-warm border-r border-slate-200/60 flex flex-col h-screen sticky top-0">
      <nav className="flex-1 px-1 md:px-5 pt-4 md:pt-6 pb-4 overflow-y-auto scroll-thin">
        <div className="hidden md:block text-[9px] font-semibold text-slate-500 tracking-[0.18em] uppercase mb-3">Operations</div>
        <div className="space-y-px">
          {nav.map((item) => (
            <NavButton key={item.id} item={item.id === 'alerts' ? { ...item, badge: alertCount ? String(alertCount) : undefined } : item} active={active === item.id} onClick={() => setActive(item.id)} />
          ))}
        </div>

        <div className="hidden md:block text-[9px] font-semibold text-slate-500 tracking-[0.18em] uppercase mb-3 mt-7">System</div>
        <div className="space-y-px">
          {bottom.map((item) => (
            <NavButton key={item.id} item={item} active={active === item.id} onClick={() => setActive(item.id)} />
          ))}
        </div>
      </nav>

      <div className="px-2 md:px-5 py-4 border-t border-slate-200/60">
        <div className="flex items-center gap-2" title={connected ? 'Backend connected' : 'Backend unavailable'}>
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-teal-400' : 'bg-amber-400'}`} />
          <span className="hidden md:inline text-[11px] text-slate-600">{connected ? 'Backend connected' : 'Backend unavailable'}</span>
        </div>
        <div className="hidden md:block mt-1.5 text-[10px] text-slate-500 font-mono">Harbour OS API</div>
      </div>
    </aside>
  );
}

function NavButton({ item, active, onClick }: { item: NavItem; active: boolean; onClick: () => void }) {
  const Icon = item.icon;
  return (
    <button
      onClick={onClick}
      title={item.label}
      aria-label={item.label}
      className={`w-full min-h-11 flex items-center justify-center md:justify-start gap-3 px-1 md:px-3 py-2.5 text-[13px] transition-colors group relative ${
        active ? 'text-navy-900 font-semibold' : 'text-slate-500 hover:text-slate-800 font-medium'
      }`}
    >
      {active && <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-ocean-500 rounded-r" />}
      <Icon className={`w-[15px] h-[15px] shrink-0 ${active ? 'text-ocean-500' : 'text-slate-400 group-hover:text-slate-500'}`} />
      <span className="hidden md:block flex-1 text-left">{item.label}</span>
      {item.badge && (
        <span className={`text-[10px] font-mono ${active ? 'text-ocean-600' : 'text-slate-400'}`}>
          {item.badge}
        </span>
      )}
    </button>
  );
}
