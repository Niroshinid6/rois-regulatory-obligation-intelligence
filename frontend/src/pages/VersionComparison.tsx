import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { GitCompare, CheckCircle2, ArrowRight, Shield, AlertTriangle, Layers, Clock } from 'lucide-react';
import { api } from '../services/api';
import { ComparisonItem, DocumentItem, ObligationChange } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const VersionComparison = () => {
  const [comparisons, setComparisons] = useState<ComparisonItem[]>([]);
  const [selectedComparison, setSelectedComparison] = useState<ComparisonItem | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [baseDocId, setBaseDocId] = useState<string>('');
  const [targetDocId, setTargetDocId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { user } = useAuth();
  const navigate = useNavigate();

  const loadData = async () => {
    setLoading(true);
    try {
      const [comps, docs] = await Promise.all([
        api.getComparisons(),
        api.getDocuments(),
      ]);
      setComparisons(comps);
      setDocuments(docs.items);

      if (comps.length > 0) {
        setSelectedComparison(comps[0]);
      }
      if (docs.items.length >= 2) {
        setBaseDocId(docs.items[0].id.toString());
        setTargetDocId(docs.items[1].id.toString());
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load comparison data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunComparison = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!baseDocId || !targetDocId) {
      alert('Please select both a base circular and an amended circular.');
      return;
    }
    if (baseDocId === targetDocId) {
      alert('Please select two distinct regulatory circulars to compare.');
      return;
    }

    setComparing(true);
    try {
      const newComp = await api.createComparison({
        base_document_id: parseInt(baseDocId),
        target_document_id: parseInt(targetDocId),
      });
      setComparisons((prev) => [newComp, ...prev]);
      setSelectedComparison(newComp);
    } catch (err: any) {
      alert(err.message || 'Comparison failed.');
    } finally {
      setComparing(false);
    }
  };

  const handleVerifyChange = async (changeId: number, type?: string) => {
    try {
      const updated = await api.verifyChange(changeId, type);
      if (selectedComparison) {
        setSelectedComparison({
          ...selectedComparison,
          changes: selectedComparison.changes.map((c) =>
            c.id === changeId ? { ...c, human_verified: true, change_type: updated.change_type } : c
          ),
        });
      }
    } catch (err: any) {
      alert(err.message || 'Failed to verify change.');
    }
  };

  const canVerify = user?.role === 'reviewer' || user?.role === 'compliance_officer' || user?.role === 'admin';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">Regulatory Version Comparison</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Deterministic and semantic diffing across regulatory circulars. Automatically classifies obligations as New, Modified, Retired, or Unchanged.
        </p>
      </div>

      {/* New Comparison Generator Bar */}
      <form onSubmit={handleRunComparison} className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <GitCompare className="h-4 w-4 text-teal-400" /> Compare Regulatory Circulars
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Base / Original Circular (v1)
            </label>
            <select
              value={baseDocId}
              onChange={(e) => setBaseDocId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-300 focus:outline-none focus:border-teal-500"
            >
              <option value="">Select Base Circular...</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.circular_number ? `${d.circular_number} — ${d.title}` : d.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Amended / Target Circular (v2)
            </label>
            <select
              value={targetDocId}
              onChange={(e) => setTargetDocId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-300 focus:outline-none focus:border-teal-500"
            >
              <option value="">Select Amended Circular...</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.circular_number ? `${d.circular_number} — ${d.title}` : d.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={comparing || !baseDocId || !targetDocId}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-2 transition-colors disabled:opacity-50 shadow-sm"
          >
            {comparing ? (
              'Analyzing Differences...'
            ) : (
              <>
                <GitCompare className="h-4 w-4" /> Run Obligation Comparison
              </>
            )}
          </button>
        </div>
      </form>

      {/* Main Results Body */}
      {selectedComparison ? (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">{selectedComparison.title}</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {selectedComparison.changes.length} obligation change items detected across regulatory versions.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Previous Comparisons:</span>
              <select
                value={selectedComparison.id}
                onChange={(e) => {
                  const found = comparisons.find((c) => c.id === parseInt(e.target.value));
                  if (found) setSelectedComparison(found);
                }}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300"
              >
                {comparisons.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Change Items Cards */}
          <div className="space-y-3">
            {selectedComparison.changes.map((change) => (
              <div
                key={change.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3 hover:border-slate-700 transition-all"
              >
                {/* Header line */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2.5">
                    <StatusBadge status={change.change_type} size="md" />
                    <span className="font-semibold text-xs text-white">
                      {change.change_explanation}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    {change.human_verified ? (
                      <span className="text-[11px] font-medium text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Human Verified
                      </span>
                    ) : (
                      canVerify && (
                        <button
                          onClick={() => handleVerifyChange(change.id)}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-teal-400 font-medium rounded text-[11px] border border-slate-700"
                        >
                          Confirm Classification
                        </button>
                      )
                    )}
                  </div>
                </div>

                {/* Side-by-side or details grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-1">
                  {/* Previous Version Obligation */}
                  <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Base Version Requirement
                      </span>
                      {change.previous_obligation && (
                        <span className="font-mono text-[10px] text-teal-400 font-bold">
                          {change.previous_obligation.obligation_code} (P.{change.previous_obligation.source_page})
                        </span>
                      )}
                    </div>
                    {change.previous_obligation ? (
                      <div>
                        <p className="text-slate-300 leading-relaxed text-xs">
                          "{change.previous_obligation.obligation_text}"
                        </p>
                        <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-3">
                          <span>Entity: <strong className="text-slate-200">{change.previous_obligation.responsible_entity || 'All REs'}</strong></span>
                          {change.previous_obligation.deadline && (
                            <span>Deadline: <strong className="text-amber-400">{change.previous_obligation.deadline}</strong></span>
                          )}
                        </div>
                      </div>
                    ) : (
                      <p className="text-slate-500 italic text-[11px] py-4">
                        None (Obligation did not exist in base version circular)
                      </p>
                    )}
                  </div>

                  {/* Target / Amended Obligation */}
                  <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-teal-400 uppercase tracking-wider">
                        Amended Version Requirement
                      </span>
                      {change.current_obligation && (
                        <span className="font-mono text-[10px] text-teal-400 font-bold">
                          {change.current_obligation.obligation_code} (P.{change.current_obligation.source_page})
                        </span>
                      )}
                    </div>
                    {change.current_obligation ? (
                      <div>
                        <p className="text-slate-300 leading-relaxed text-xs">
                          "{change.current_obligation.obligation_text}"
                        </p>
                        <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-3">
                          <span>Entity: <strong className="text-slate-200">{change.current_obligation.responsible_entity || 'All REs'}</strong></span>
                          {change.current_obligation.deadline && (
                            <span>Deadline: <strong className="text-amber-400">{change.current_obligation.deadline}</strong></span>
                          )}
                        </div>
                        <div className="mt-2 pt-2 border-t border-slate-800/60 flex justify-end">
                          <button
                            onClick={() => navigate(`/evidence/${change.current_obligation?.id}`)}
                            className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
                          >
                            Inspect Evidence <ArrowRight className="h-3 w-3" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-slate-500 italic text-[11px] py-4">
                        Retired (Obligation eliminated or omitted in amended circular)
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-slate-400 bg-slate-900 border border-slate-800 rounded-xl">
          <GitCompare className="h-10 w-10 text-slate-600 mx-auto mb-2" />
          <p className="text-xs">No comparison history found. Select two circulars above to begin.</p>
        </div>
      )}
    </div>
  );
};
