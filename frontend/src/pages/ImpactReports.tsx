import { useState, useEffect } from 'react';
import { BarChart3, Download, Plus, FileText, CheckCircle2, AlertCircle, Clock, Shield } from 'lucide-react';
import { api } from '../services/api';
import { ImpactReportItem, DocumentItem } from '../types';

export const ImpactReports = () => {
  const [reports, setReports] = useState<ImpactReportItem[]>([]);
  const [selectedReport, setSelectedReport] = useState<ImpactReportItem | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadReports = async () => {
    setLoading(true);
    try {
      const [reps, docs] = await Promise.all([
        api.getReports(),
        api.getDocuments(),
      ]);
      setReports(reps);
      setDocuments(docs.items);
      if (reps.length > 0) {
        setSelectedReport(reps[0]);
      }
      if (docs.items.length > 0) {
        setSelectedDocId(docs.items[0].id.toString());
      }
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDocId) return;

    setGenerating(true);
    try {
      const newRep = await api.generateReport({
        document_id: parseInt(selectedDocId),
      });
      setReports((prev) => [newRep, ...prev]);
      setSelectedReport(newRep);
    } catch (err: any) {
      alert(err.message || 'Failed to generate report.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Regulatory Impact Reports</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit-grade compliance syntheses aggregating verified obligations, control domain distributions, and action items.
          </p>
        </div>

        {selectedReport && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => window.print()}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg text-xs border border-slate-700"
            >
              Print Report
            </button>
            <button
              onClick={() => api.downloadReport(selectedReport.id, 'pdf').catch((err) => alert(err.message))}
              className="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Download className="h-4 w-4" /> Export PDF
            </button>
            <button
              onClick={() => api.downloadReport(selectedReport.id, 'json').catch((err) => alert(err.message))}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg text-xs border border-slate-700 flex items-center gap-1.5"
            >
              <Download className="h-4 w-4" /> Export JSON
            </button>
          </div>
        )}
      </div>

      {/* Generator & Selector Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Selector */}
        <div className="flex items-center gap-2 flex-1">
          <span className="text-xs text-slate-400 font-semibold whitespace-nowrap">Saved Reports:</span>
          <select
            value={selectedReport?.id || ''}
            onChange={(e) => {
              const found = reports.find((r) => r.id === parseInt(e.target.value));
              if (found) setSelectedReport(found);
            }}
            className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-teal-500"
          >
            {reports.map((r) => (
              <option key={r.id} value={r.id}>
                {r.title}
              </option>
            ))}
          </select>
        </div>

        {/* Generate new */}
        <form onSubmit={handleGenerateReport} className="flex items-center gap-2">
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-teal-500"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.circular_number || d.title}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={generating || !selectedDocId}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-teal-400 border border-teal-500/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap disabled:opacity-50"
          >
            <Plus className="h-3.5 w-3.5" /> Generate
          </button>
        </form>
      </div>

      {/* Report Document Presentation */}
      {selectedReport ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-6 text-xs text-slate-300 print:bg-white print:text-black">
          {/* Header */}
          <div className="border-b border-slate-800 pb-5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-teal-400 uppercase tracking-widest font-bold">
                ROIS REGULATORY INTELLIGENCE ASSESSMENT
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                Generated: {new Date(selectedReport.created_at).toLocaleDateString()}
              </span>
            </div>
            <h1 className="text-xl font-bold text-white mt-1.5 tracking-tight print:text-black">
              {selectedReport.title}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Authority: IFSCA (International Financial Services Centres Authority) • GIFT City
            </p>
          </div>

          {/* Executive Summary */}
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 print:text-black">
              Executive Compliance Overview
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
              {selectedReport.executive_summary}
            </p>
          </div>

          {/* Operational Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Total Obligations</span>
              <div className="text-xl font-bold text-white mt-1">{selectedReport.metrics.total_obligations}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Reviewer Approved</span>
              <div className="text-xl font-bold text-emerald-400 mt-1">{selectedReport.metrics.approved_obligations}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Pending Verification</span>
              <div className="text-xl font-bold text-amber-400 mt-1">{selectedReport.metrics.pending_reviews}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Control Domains</span>
              <div className="text-xl font-bold text-teal-400 mt-1">{selectedReport.metrics.impacted_control_count}</div>
            </div>
          </div>

          {/* Key Mandated Action Items Table */}
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 print:text-black flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-teal-400" /> High-Priority Compliance Action Items
            </h3>
            <div className="border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-950/60 border-b border-slate-800 text-slate-400 text-[11px]">
                    <th className="py-2.5 px-3 font-semibold">Code</th>
                    <th className="py-2.5 px-3 font-semibold">Responsible Entity</th>
                    <th className="py-2.5 px-3 font-semibold">Mandated Action</th>
                    <th className="py-2.5 px-3 font-semibold">Deadline</th>
                    <th className="py-2.5 px-3 font-semibold text-center">Page</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {selectedReport.report_data.high_priority_action_items?.map((item: any, i: number) => (
                    <tr key={i} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-mono font-bold text-teal-400 whitespace-nowrap">
                        {item.obligation_code}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-slate-200">
                        {item.responsible_entity}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300 leading-relaxed">
                        {item.action}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-amber-300 whitespace-nowrap">
                        {item.deadline}
                      </td>
                      <td className="py-2.5 px-3 text-center font-mono text-slate-400">
                        P.{item.page}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Control Domain Distribution */}
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 print:text-black">
              Impacted Internal Control Categories
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {Object.entries(selectedReport.report_data.control_distribution || {}).map(([cat, count]: [string, any]) => (
                <div key={cat} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                  <span className="text-slate-200 font-medium">{cat}</span>
                  <span className="font-mono font-bold text-teal-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    {count} requirements
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Notice of Legal Limitation */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong className="text-slate-300 block mb-1">Notice of Regulatory Governance Limitation:</strong>
            {selectedReport.report_data.legal_limitations_notice}
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-slate-400 bg-slate-900 border border-slate-800 rounded-xl">
          <FileText className="h-10 w-10 text-slate-600 mx-auto mb-2" />
          <p className="text-xs">No impact reports found. Generate one using the selector above.</p>
        </div>
      )}
    </div>
  );
};
