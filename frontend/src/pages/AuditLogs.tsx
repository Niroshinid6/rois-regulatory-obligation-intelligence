import { useState, useEffect } from 'react';
import { History, Shield, Filter, Search, User, FileText, CheckCircle } from 'lucide-react';
import { api } from '../services/api';
import { AuditLogItem } from '../types';

export const AuditLogs = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [resourceFilter, setResourceFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs({
        resource_type: resourceFilter || undefined,
        action: actionFilter || undefined,
        limit: 100,
      });
      setLogs(data);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [resourceFilter, actionFilter]);

  const getActionBadge = (action: string) => {
    if (action.includes('approved') || action.includes('verified')) {
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    }
    if (action.includes('upload') || action.includes('create')) {
      return 'bg-teal-500/10 text-teal-400 border-teal-500/30';
    }
    if (action.includes('login') || action.includes('init')) {
      return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
    }
    if (action.includes('delete') || action.includes('rejected')) {
      return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    }
    return 'bg-slate-800 text-slate-300 border-slate-700';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">Audit Trail & Activity Ledger</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Immutable system ledger capturing regulatory extractions, human reviewer decisions, version diffs, and authentication events.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-center gap-3 text-xs">
        <select
          value={resourceFilter}
          onChange={(e) => setResourceFilter(e.target.value)}
          className="w-full sm:w-auto bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-teal-500"
        >
          <option value="">All Resource Types</option>
          <option value="document">Documents</option>
          <option value="obligation">Obligations</option>
          <option value="comparison">Comparisons</option>
          <option value="obligation_control">Controls</option>
          <option value="impact_report">Impact Reports</option>
          <option value="user">Users</option>
          <option value="system">System</option>
        </select>

        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="w-full sm:w-auto bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-teal-500"
        >
          <option value="">All Actions</option>
          <option value="document_upload">Document Upload</option>
          <option value="obligation_approved">Obligation Approved</option>
          <option value="obligation_corrected">Obligation Corrected</option>
          <option value="comparison_created">Comparison Created</option>
          <option value="report_generated">Report Generated</option>
          <option value="user_login">User Login</option>
        </select>

        <span className="text-slate-500 ml-auto font-mono text-[11px]">
          Ledger entries: <strong className="text-teal-400 font-bold">{logs.length}</strong>
        </span>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px] bg-slate-950/40">
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-3 font-semibold">Actor / User</th>
                <th className="py-3 px-3 font-semibold">Action</th>
                <th className="py-3 px-3 font-semibold">Target Resource</th>
                <th className="py-3 px-4 font-semibold">Event Payload / Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400 font-sans text-xs">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500 mx-auto mb-2"></div>
                    Loading audit ledger...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400 font-sans text-xs">
                    <History className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    No audit log records found for this filter.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-slate-200 whitespace-nowrap font-sans font-medium">
                      {log.user_name || 'System'}
                      {log.user_email && (
                        <div className="text-[10px] text-slate-500 font-mono">{log.user_email}</div>
                      )}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className={`inline-block px-2 py-0.5 rounded-full border text-[10px] font-medium capitalize font-sans ${getActionBadge(log.action)}`}>
                        {log.action.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-300 whitespace-nowrap">
                      <span className="text-teal-400 font-bold">{log.resource_type}</span>
                      {log.resource_id && (
                        <span className="text-slate-500"> #{log.resource_id}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-sans text-xs max-w-md truncate">
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
