import type { StatItem, Trend } from '@/data/dashboard';

function MiniChart({ data, trend, reduced }: { data: number[]; trend: Trend; reduced: boolean }) {
  if (data.length < 2) return null;
  const width = 144;
  const height = 30;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  });
  const path = `M ${points.join(' L ')}`;
  const color = trend === 'up' ? '#3aa6a0' : trend === 'down' ? '#c44545' : '#718096';

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} fill="none" aria-label="Historical trend">
      <path d={path} stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
        style={reduced ? undefined : { strokeDasharray: 220, animation: 'drawLine 1.5s ease-out both' }} />
    </svg>
  );
}

export default function StatStrip({ stats, reducedMotion }: { stats: StatItem[]; reducedMotion: boolean }) {
  const hasHistory = stats.some((stat) => stat.spark.length > 1);
  return (
    <>
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-5">
        {stats.map((stat) => (
          <div key={stat.label} className="min-w-0 border-l border-slate-200 pl-4 first:border-0 first:pl-0">
            <div className="text-xs font-semibold text-slate-600 tracking-wide mb-1">{stat.label}</div>
            <div className="text-2xl sm:text-[26px] font-display font-semibold text-navy-900 tracking-tight leading-tight">
              {stat.value}
            </div>
            <div className="mt-1 text-xs text-slate-600">{stat.change}</div>
            {stat.spark.length > 1 && <div className="mt-2"><MiniChart data={stat.spark} trend={stat.trend} reduced={reducedMotion} /></div>}
          </div>
        ))}
      </div>
      {!hasHistory && <p className="mt-3 text-xs text-slate-600">Historical comparisons are not available from the current API.</p>}
    </>
  );
}
