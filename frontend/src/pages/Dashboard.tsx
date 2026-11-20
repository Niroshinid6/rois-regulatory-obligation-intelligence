import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Layers,
  Clock,
  CheckCircle,
  GitCompare,
  Sliders,
  UploadCloud,
  Search,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../services/api';
import { DashboardMetrics } from '../types';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';

export const Dashboard = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await api.getDashboardMetrics();
        setMetrics(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard operational metrics.');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-xs">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500 mb-3"></div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 text-center">
        <AlertTriangle className="h-8 w-8 text-amber-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-white">Error Loading Dashboard</h3>
        <p className="text-xs text-slate-400 mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl bg-gradient-to-r from-slate-900 via-slate-900 to-navy-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-white tracking-tight">Compliance Intelligence Overview</h2>
            <span className="text-[10px] bg-teal-500/10 text-teal-400 border border-teal-500/30 px-2 py-0.5 rounded font-mono font-medium">
              Live IFSCA Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time regulatory obligation extraction, coordinate evidence anchoring, and version delta tracking.
          </p>
        </div>

        {/* Quick Action Shortcuts */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/upload')}
            className="px-3 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <UploadCloud className="h-4 w-4" /> Upload Circular
          </button>
          <button
            onClick={() => navigate('/review-queue')}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <Clock className="h-4 w-4 text-amber-400" /> Review Queue ({metrics.pending_reviews})
          </button>
        </div>
      </div>

      {/* Operational Metric Cards (Calculated directly from Database) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Documents"
          value={metrics.total_documents}
          subtitle={`${metrics.processed_documents} processed with layout`}
          icon={FileText}
          badge="100% IFSCA"
          badgeColor="teal"
          onClick={() => navigate('/documents')}
        />
        <StatCard
          title="Extracted Obligations"
          value={metrics.total_obligations}
          subtitle={`${metrics.approved_obligations} validated by reviewers`}
          icon={Layers}
          badge="Evidence Anchored"
          badgeColor="emerald"
          onClick={() => navigate('/obligations')}
        />
        <StatCard
          title="Pending Reviews"
          value={metrics.pending_reviews}
          subtitle="Awaiting compliance sign-off"
          icon={Clock}
          badge={metrics.pending_reviews > 0 ? 'Requires Action' : 'Cleared'}
          badgeColor={metrics.pending_reviews > 0 ? 'amber' : 'emerald'}
          onClick={() => navigate('/review-queue')}
        />
        <StatCard
          title="Impacted Controls"
          value={metrics.impacted_controls_count}
          subtitle="Taxonomy control domains"
          icon={Sliders}
          badge="Active Matrix"
          badgeColor="blue"
          onClick={() => navigate('/controls')}
        />
      </div>

      {/* Version Change Delta Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">New Obligations</span>
            <div className="text-2xl font-bold text-white mt-1">{metrics.new_obligations}</div>
            <p className="text-[11px] text-slate-400">Newly mandated requirements</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="h-5 w-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Modified Obligations</span>
            <div className="text-2xl font-bold text-white mt-1">{metrics.modified_obligations}</div>
            <p className="text-[11px] text-slate-400">Deadlines or scopes adjusted</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <GitCompare className="h-5 w-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Retired Obligations</span>
            <div className="text-2xl font-bold text-white mt-1">{metrics.retired_obligations}</div>
            <p className="text-[11px] text-slate-400">Superseded or omitted clauses</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
            <Layers className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Two Column Section: Recent Documents & Review Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents Table */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <FileText className="h-4 w-4 text-teal-400" /> Recent Regulatory Circulars
            </h3>
            <button
              onClick={() => navigate('/documents')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
            >
              View All <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                  <th className="pb-2 font-medium">Circular Title</th>
                  <th className="pb-2 font-medium">Reference</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium text-right">Obligations</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {metrics.recent_documents.map((doc) => (
                  <tr
                    key={doc.id}
                    onClick={() => navigate(`/documents`)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 pr-2 font-medium text-slate-200 truncate max-w-[200px]">
                      {doc.title}
                    </td>
                    <td className="py-2.5 font-mono text-[11px] text-slate-400">
                      {doc.circular_number || 'N/A'}
                    </td>
                    <td className="py-2.5">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="py-2.5 text-right font-mono font-bold text-teal-400">
                      {doc.obligation_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending Human Reviews Queue */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-400" /> Pending Review Items
            </h3>
            <button
              onClick={() => navigate('/review-queue')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
            >
              Review Inbox <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          <div className="space-y-3">
            {metrics.pending_review_items.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-xs">
                <CheckCircle className="h-6 w-6 text-emerald-400 mx-auto mb-1.5" />
                All extracted obligations have been verified.
              </div>
            ) : (
              metrics.pending_review_items.map((item) => (
                <div
                  key={item.id}
                  onClick={() => navigate(`/evidence/${item.id}`)}
                  className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-slate-700 cursor-pointer transition-all"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-[11px] font-bold text-teal-400">{item.obligation_code}</span>
                    <span className="text-[10px] text-slate-400">Page {item.source_page}</span>
                  </div>
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {item.required_action}
                  </p>
                  <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
                    <span>Entity: <strong className="text-slate-300">{item.responsible_entity || 'All REs'}</strong></span>
                    <span className="text-amber-400 flex items-center gap-1 font-medium">
                      Inspect Evidence <ArrowRight className="h-2.5 w-2.5" />
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Regulatory Changes Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <GitCompare className="h-4 w-4 text-teal-400" /> Recent Regulatory Changes Detected
          </h3>
          <button
            onClick={() => navigate('/compare')}
            className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
          >
            Compare Versions <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                <th className="pb-2 font-medium">Type</th>
                <th className="pb-2 font-medium">Detected Change Description</th>
                <th className="pb-2 font-medium">Target Obligation</th>
                <th className="pb-2 font-medium text-right">Human Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {metrics.recent_changes.map((ch) => (
                <tr key={ch.id} className="hover:bg-slate-800/40">
                  <td className="py-2.5">
                    <StatusBadge status={ch.change_type} />
                  </td>
                  <td className="py-2.5 font-medium text-slate-300 max-w-md">
                    {ch.change_explanation}
                  </td>
                  <td className="py-2.5 font-mono text-[11px] text-teal-400">
                    {ch.current_code || ch.previous_code || 'N/A'}
                  </td>
                  <td className="py-2.5 text-right">
                    {ch.human_verified ? (
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <CheckCircle className="h-3.5 w-3.5" /> Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                        Pending Sign-off
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
