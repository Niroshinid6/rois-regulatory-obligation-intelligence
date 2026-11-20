import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: LucideIcon;
  badge?: string;
  badgeColor?: 'teal' | 'amber' | 'emerald' | 'blue' | 'purple' | 'rose';
  onClick?: () => void;
}

export const StatCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  badgeColor = 'teal',
  onClick,
}: StatCardProps) => {
  const badgeColors = {
    teal: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  };

  return (
    <div
      onClick={onClick}
      className={`bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition-all ${
        onClick ? 'cursor-pointer hover:bg-slate-900' : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60 text-teal-400">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-bold text-white tracking-tight">{value}</span>
        {badge && (
          <span className={`text-xs px-2 py-0.5 rounded-full border ${badgeColors[badgeColor]}`}>
            {badge}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
};
