interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge = ({ status, size = 'sm' }: StatusBadgeProps) => {
  const norm = (status || '').toLowerCase().replace(/_/g, ' ');

  const getStyle = () => {
    switch (norm) {
      // Review statuses
      case 'approved':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'pending':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'corrected':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'rejected':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'requires investigation':
      case 'requires review':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';

      // Document processing
      case 'processed':
        return 'bg-teal-500/10 text-teal-300 border-teal-500/30';
      case 'requires ocr':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'processing':
      case 'queued':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
      case 'failed':
        return 'bg-red-500/10 text-red-400 border-red-500/30';

      // Comparison change types
      case 'new':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 font-semibold';
      case 'modified':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/40 font-semibold';
      case 'retired':
        return 'bg-slate-500/20 text-slate-400 border-slate-500/40 font-semibold';
      case 'unchanged':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';

      // Evidence anchoring
      case 'anchored':
        return 'bg-teal-500/15 text-teal-300 border-teal-500/40';
      case 'unverified':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';

      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const sz = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center font-medium rounded-full border capitalize ${getStyle()} ${sz}`}>
      {norm}
    </span>
  );
};
