import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckSquare, CheckCircle, XCircle, ArrowRight, Clock, Shield, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { ObligationItem } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';

export const ReviewQueue = () => {
  const [pendingItems, setPendingItems] = useState<ObligationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const navigate = useNavigate();

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const data = await api.getObligations({
        review_status: 'pending',
        limit: 100,
      });
      setPendingItems(data.items);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleQuickApprove = async (id: number, code: string) => {
    try {
      await api.reviewObligation(id, {
        action: 'approved',
        comments: 'Quick verified from review queue.',
      });
      setPendingItems((prev) => prev.filter((item) => item.id !== id));
      setActionSuccess(`Obligation ${code} approved successfully.`);
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to approve obligation.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Human Oversight Review Queue</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Active verification inbox for compliance officers to inspect extracted obligations, anchor evidence, and approve regulatory findings.
          </p>
        </div>

        <div className="text-xs text-slate-400 font-mono self-start sm:self-auto">
          Pending Verification: <strong className="text-amber-400 font-bold">{pendingItems.length}</strong> items
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs flex items-center gap-2">
          <CheckCircle className="h-4 w-4" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Queue Items List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500 mx-auto mb-2"></div>
            Loading review queue...
          </div>
        ) : pendingItems.length === 0 ? (
          <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl">
            <CheckCircle className="h-10 w-10 text-emerald-400 mx-auto mb-2" />
            <h3 className="text-sm font-semibold text-white">Review Inbox Cleared</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              All extracted candidate obligations have been verified by compliance reviewers.
            </p>
          </div>
        ) : (
          pendingItems.map((item) => (
            <div
              key={item.id}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition-all space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-teal-400">{item.obligation_code}</span>
                  <StatusBadge status={item.review_status} />
                  <span className="text-[11px] text-slate-400 font-mono">
                    Page {item.source_page} • {item.circular_number || 'IFSCA Circular'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400">Confidence:</span>
                  <span className="font-mono text-xs font-bold text-teal-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                    {Math.round(item.confidence_score * 100)}%
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Mandatory Required Action
                </span>
                <p className="text-xs font-semibold text-slate-200 mt-0.5">
                  {item.required_action}
                </p>
                <p className="text-[11px] text-slate-400 italic mt-1 leading-relaxed">
                  "{item.obligation_text}"
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs pt-1">
                <div>
                  <span className="text-slate-500 text-[11px]">Responsible Entity:</span>{' '}
                  <strong className="text-slate-200">{item.responsible_entity || 'All Regulated Entities'}</strong>
                </div>
                <div>
                  <span className="text-slate-500 text-[11px]">Deadline:</span>{' '}
                  {item.deadline ? (
                    <strong className="text-amber-400 font-mono">{item.deadline}</strong>
                  ) : (
                    <span className="text-slate-500 italic">None stated</span>
                  )}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
                <button
                  onClick={() => navigate(`/evidence/${item.id}`)}
                  className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
                >
                  Inspect Source PDF & Detailed Form <ArrowRight className="h-3 w-3" />
                </button>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleQuickApprove(item.id, item.obligation_code)}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs flex items-center gap-1.5 transition-colors shadow-sm"
                  >
                    <CheckCircle className="h-3.5 w-3.5" /> Approve
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
