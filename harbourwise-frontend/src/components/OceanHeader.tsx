import { useEffect, useRef, useState } from 'react';
import {
  Bell, Search, ChevronDown, Anchor, Settings,
  LifeBuoy, X,
} from 'lucide-react';
import type { AlertItem } from '@/data/dashboard';

/* Base wave path: fills from top to wavy bottom edge */
function makeBaseWavePath(width: number, baseY: number, amplitude: number, wavelength: number, seed: number): string {
  const segments = Math.ceil(width / wavelength);
  const totalW = segments * wavelength;
  let d = `M 0 0 L 0 ${baseY}`;
  for (let i = 0; i < segments; i++) {
    const x1 = i * wavelength + wavelength * 0.5;
    const variance = 0.55 + 0.45 * Math.sin((i + seed) * 1.7);
    const y1 = baseY - amplitude * variance;
    const x2 = (i + 1) * wavelength;
    const y2 = baseY + Math.sin((i + seed) * 0.9) * amplitude * 0.14;
    d += ` Q ${x1} ${y1} ${x2} ${y2}`;
  }
  d += ` L ${totalW} 0 Z`;
  return d;
}

/* Layer wave path: fills only from clipY down to wavy edge */
function makeLayerWavePath(width: number, clipY: number, baseY: number, amplitude: number, wavelength: number, seed: number): string {
  const segments = Math.ceil(width / wavelength);
  const totalW = segments * wavelength;
  let d = `M 0 ${clipY} L 0 ${baseY}`;
  for (let i = 0; i < segments; i++) {
    const x1 = i * wavelength + wavelength * 0.5;
    const variance = 0.55 + 0.45 * Math.sin((i + seed) * 1.7);
    const y1 = baseY - amplitude * variance;
    const x2 = (i + 1) * wavelength;
    const y2 = baseY + Math.sin((i + seed) * 0.9) * amplitude * 0.14;
    d += ` Q ${x1} ${y1} ${x2} ${y2}`;
  }
  d += ` L ${totalW} ${clipY} Z`;
  return d;
}

function FishingVessel({ reduced = false }: { reduced?: boolean }) {
  return (
    <svg width="54" height="34" viewBox="0 0 54 34" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g style={reduced ? { opacity: 0.18 } : undefined}>
        <ellipse cx="4" cy="29" rx="11" ry="1.3" fill="white" opacity="0.18" />
        <ellipse cx="1" cy="30" rx="6" ry="0.9" fill="white" opacity="0.1" />
      </g>
      <path d="M7 23 L47 23 L42 31 L12 31 Z" fill="#334155" />
      <path d="M7 23 L47 23 L45 26 L9 26 Z" fill="#64748b" />
      <line x1="9" y1="26" x2="45" y2="26" stroke="#475569" strokeWidth="0.3" />
      <line x1="11" y1="28" x2="43" y2="28" stroke="#071a2b" strokeWidth="0.4" opacity="0.35" />
      <rect x="18" y="15" width="16" height="8" rx="0.8" fill="#94a3b8" />
      <rect x="18" y="15" width="16" height="2" rx="0.5" fill="#cbd5e1" />
      <rect x="20" y="17" width="4.5" height="3.5" rx="0.3" fill="#071a2b" opacity="0.55" />
      <rect x="27" y="17" width="4.5" height="3.5" rx="0.3" fill="#071a2b" opacity="0.55" />
      <line x1="26" y1="4" x2="26" y2="15" stroke="#475569" strokeWidth="0.9" />
      <circle cx="26" cy="4" r="1.1" fill="#fbbf24" />
      <line x1="23" y1="7" x2="29" y2="7" stroke="#475569" strokeWidth="0.5" />
      <line x1="26" y1="7" x2="26" y2="9" stroke="#475569" strokeWidth="0.5" />
      <line x1="9" y1="21" x2="9" y2="23" stroke="#475569" strokeWidth="0.35" />
      <line x1="14" y1="21" x2="14" y2="23" stroke="#475569" strokeWidth="0.35" />
      <line x1="40" y1="21" x2="40" y2="23" stroke="#475569" strokeWidth="0.35" />
      <line x1="45" y1="21" x2="45" y2="23" stroke="#475569" strokeWidth="0.35" />
      <path d="M47 23 L45 25 L42 25" stroke="#475569" strokeWidth="0.3" fill="none" />
    </svg>
  );
}

function LogoMark() {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
      <path d="M15 5 L17 11 L15 10 L13 11 Z" fill="#3aa6a0" />
      <rect x="13.5" y="11" width="3" height="10" rx="0.4" fill="white" opacity="0.85" />
      <path d="M12 21 L18 21 L17 25 L13 25 Z" fill="white" opacity="0.55" />
      <circle cx="15" cy="14" r="1.3" fill="#3aa6a0" />
      <path d="M7 22 Q10 20 13 22 T19 22 T23 22" stroke="#3aa6a0" strokeWidth="0.6" fill="none" opacity="0.5" />
    </svg>
  );
}

interface OceanHeaderProps {
  harbour: string;
  setHarbour: (h: string) => void;
  harbours: string[];
  alerts: AlertItem[];
}

export default function OceanHeader({ harbour, setHarbour, harbours, alerts }: OceanHeaderProps) {
  const [harbourOpen, setHarbourOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [time, setTime] = useState('');
  const [reducedMotion, setReducedMotion] = useState(false);
  const harbourRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' }));
    tick();
    const id = setInterval(tick, 30000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mq.matches);
    const handler = () => setReducedMotion(mq.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (harbourRef.current && !harbourRef.current.contains(e.target as Node)) setHarbourOpen(false);
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const SVG_W = 1600;
  const SVG_H = 160;
  const TILED_W = SVG_W * 2;

  const baseShapePath = makeBaseWavePath(TILED_W, 100, 18, 320, 2);
  const wave1Path = makeLayerWavePath(TILED_W, 78, 96, 14, 280, 5);
  const wave2Path = makeLayerWavePath(TILED_W, 84, 104, 10, 220, 9);
  const wave3Path = makeLayerWavePath(TILED_W, 90, 112, 7, 170, 13);

  return (
    <header className="relative z-50 select-none">
      <div className="relative w-full" style={{ height: '120px' }}>
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          preserveAspectRatio="none"
          style={{ display: 'block' }}
        >
          <defs>
            <linearGradient id="navyGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#071a2b" />
              <stop offset="50%" stopColor="#091e32" />
              <stop offset="100%" stopColor="#0b2640" />
            </linearGradient>
          </defs>
          <path d={baseShapePath} fill="url(#navyGrad)" />
          <g className="wave-anim" style={{ animation: reducedMotion ? 'none' : 'waveMoveA 16s linear infinite' }}>
            <path d={wave1Path} fill="#0a2540" opacity={0.7} />
          </g>
          <g className="wave-anim" style={{ animation: reducedMotion ? 'none' : 'waveMoveB 12s linear infinite', animationDelay: '-3s' }}>
            <path d={wave2Path} fill="#1268a5" opacity={0.25} />
          </g>
          <g className="wave-anim" style={{ animation: reducedMotion ? 'none' : 'waveMoveC 10s linear infinite', animationDelay: '-5s' }}>
            <path d={wave3Path} fill="#3aa6a0" opacity={0.1} />
          </g>
          {[60, 220, 440, 660, 900, 1120, 1300, 1480].map((x, i) => (
            <circle
              key={i}
              cx={x}
              cy={94 + (i % 2) * 3}
              r={1}
              fill="white"
              className="foam-anim"
              opacity={reducedMotion ? 0.2 : undefined}
              style={{
                animation: reducedMotion ? 'none' : `foamPulse ${5 + (i % 3)}s ease-in-out infinite`,
                animationDelay: `${i * 0.7}s`,
              }}
            />
          ))}
        </svg>

        {/* Navbar content */}
        <div className="absolute inset-0 px-5 sm:px-8 pt-3.5 z-20">
          <div className="flex items-center justify-between gap-4">
            {/* Brand */}
            <div className="flex items-center gap-2.5 shrink-0">
              <LogoMark />
              <div className="leading-none">
                <div className="font-display font-extrabold text-white text-[15px] sm:text-base tracking-[0.04em]">
                  KALASTUS
                </div>
                <div className="text-[8px] font-medium text-teal-200/40 tracking-[0.22em] uppercase mt-1 hidden sm:block">
                  Fishing Harbour Network
                </div>
              </div>
            </div>

            {/* Search */}
            <div className="hidden md:flex flex-1 max-w-xs mx-6">
              <div className="relative w-full group">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 group-focus-within:text-ocean-400 transition-colors" />
                <input
                  type="text"
                  placeholder="Search vessels, landings, species…"
                  className="w-full bg-white/[0.03] border-b border-white/[0.08] pl-8 pr-3 py-1.5 text-[13px] text-white placeholder:text-slate-500 focus:outline-none focus:border-ocean-400 transition-all"
                />
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2.5 shrink-0">
              {/* Harbour selector */}
              <div ref={harbourRef} className="relative">
                <button
                  onClick={() => setHarbourOpen((v) => !v)}
                  className="flex items-center gap-1.5 text-[13px] text-slate-300 hover:text-white transition-colors"
                >
                  <Anchor className="w-3.5 h-3.5 text-teal-400/60" />
                  <span className="hidden sm:inline font-medium">{harbour}</span>
                  <ChevronDown className={`w-3 h-3 text-slate-500 transition-transform duration-200 ${harbourOpen ? 'rotate-180' : ''}`} />
                </button>
                {harbourOpen && (
                  <div className="absolute right-0 mt-3 w-48 bg-white border border-slate-200 py-1 z-50 overflow-hidden shadow-xl">
                    {harbours.map((h) => (
                      <button
                        key={h}
                        onClick={() => { setHarbour(h); setHarbourOpen(false); }}
                        className={`w-full text-left px-4 py-2 text-[13px] transition-colors flex items-center gap-2 ${
                          harbour === h ? 'text-ocean-600 font-semibold' : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <Anchor className={`w-3 h-3 ${harbour === h ? 'text-ocean-500' : 'text-slate-300'}`} />
                        {h}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="w-px h-4 bg-white/10 hidden sm:block" />

              {/* Notifications */}
              <div ref={notifRef} className="relative">
                <button
                  onClick={() => setNotifOpen((v) => !v)}
                  className="relative text-slate-300 hover:text-white transition-colors"
                >
                  <Bell className="w-4 h-4" />
                  {alerts.length > 0 && (
                    <span className="absolute -top-1 -right-1.5 w-3.5 h-3.5 bg-teal-400 rounded-full text-[8px] font-bold text-navy-900 flex items-center justify-center">
                      {alerts.length}
                    </span>
                  )}
                </button>
                {notifOpen && (
                  <div className="absolute right-0 mt-3 w-72 bg-white border border-slate-200 py-2 z-50 shadow-xl">
                    <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                      <span className="font-display font-semibold text-[13px] text-slate-800">Notifications</span>
                      <button onClick={() => setNotifOpen(false)} className="text-slate-400 hover:text-slate-600">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="max-h-60 overflow-y-auto scroll-thin">
                      {alerts.length ? alerts.map((alert) => (
                        <NotifRow key={alert.id} color={alert.level === 'critical' ? 'bg-red-500' : alert.level === 'warning' ? 'bg-amber-400' : 'bg-ocean-400'} title={alert.title} detail={alert.detail} time={alert.time} />
                      )) : <div className="px-4 py-4 text-xs text-slate-500">No active notifications.</div>}
                    </div>
                  </div>
                )}
              </div>

              {/* Settings */}
              <button className="text-slate-400 hover:text-white transition-colors hidden sm:block">
                <Settings className="w-4 h-4" />
              </button>

              {/* Help */}
              <button className="text-slate-400 hover:text-white transition-colors hidden sm:block">
                <LifeBuoy className="w-4 h-4" />
              </button>

              <div className="w-px h-4 bg-white/10 hidden lg:block" />

              {/* Clock */}
              <div className="hidden lg:flex items-center gap-1.5">
                <span className="text-[11px] font-mono text-slate-400">{time}</span>
                <span className="text-[9px] text-slate-600">IST</span>
              </div>

              {/* User */}
              <div className="flex items-center gap-2.5 pl-1">
                <div className="w-7 h-7 rounded-full bg-ocean-500 flex items-center justify-center text-white font-semibold text-[11px]">
                  HW
                </div>
                <div className="hidden xl:block leading-none">
                  <div className="text-[12px] font-medium text-white">KALASTUS</div>
                  <div className="text-[9px] text-slate-500 mt-0.5">Operations</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Moving fishing vessel */}
        <div
          className="absolute pointer-events-none ship-anim"
          style={{
            top: '70px',
            left: 0,
            animation: reducedMotion ? 'none' : 'shipSail 24s linear infinite',
            transform: reducedMotion ? 'translateX(20%)' : undefined,
            zIndex: 15,
          }}
        >
          <div
            className="ship-bob-anim"
            style={{
              animation: reducedMotion ? 'none' : 'shipBob 4.5s ease-in-out infinite',
              transform: reducedMotion ? 'translateY(0) rotate(0deg)' : undefined,
            }}
          >
            <FishingVessel reduced={reducedMotion} />
          </div>
        </div>
      </div>
    </header>
  );
}

function NotifRow({ color, title, detail, time }: { color: string; title: string; detail: string; time: string }) {
  return (
    <div className="px-4 py-2.5 hover:bg-slate-50 transition-colors cursor-pointer flex gap-3">
      <div className={`w-1.5 h-1.5 rounded-full ${color} mt-2 shrink-0`} />
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-medium text-slate-800">{title}</div>
        <div className="text-xs text-slate-500 truncate mt-0.5">{detail}</div>
      </div>
      <div className="text-[10px] text-slate-400 shrink-0">{time}</div>
    </div>
  );
}
