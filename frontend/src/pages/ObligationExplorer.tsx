import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Eye, Filter, Download, ArrowRight, Shield, Clock } from 'lucide-react';
import { api } from '../services/api';
import { ObligationItem, DocumentItem } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';

export const ObligationExplorer = () => {
  const [obligations, setObligations] = useState<ObligationItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const documentId = searchParams.get('document_id') || '';
  const reviewStatus = searchParams.get('review_status') || '';
  const entity = searchParams.get('entity') || '';
  const search = searchParams.get('search') || '';

  const [localSearch, setLocalSearch] = useState(search);

  useEffect(() => {
    // Fetch documents for the filter dropdown
    api.getDocuments().then((res) => setDocuments(res.items)).catch(() => {});
  }, []);

  const fetchObligations = async () => {
    setLoading(true);
    try {
      const data = await api.getObligations({
        document_id: documentId ? parseInt(documentId) : undefined,
        review_status: reviewStatus || undefined,
        entity: entity || undefined,
        search: search || undefined,
        limit: 100,
      });
      setObligations(data.items);
      setTotal(data.total);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObligations();
  }, [documentId, reviewStatus, entity, search]);

  const updateParam = (key: string, val: string) => {
    const next = new URLSearchParams(searchParams);
    if (val) {
      next.set(key, val);
    } else {
      next.delete(key);
    }
    setSearchParams(next);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateParam('search', localSearch);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Regulatory Obligation Explorer</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Searchable repository of mandatory compliance directives extracted from authentic IFSCA circulars.
          </p>
        </div>

        <div className="text-xs text-slate-400 font-mono self-start sm:self-auto">
          Showing <strong className="text-teal-400 font-bold">{obligations.length}</strong> of {total} obligations
        </div>
      </div>

      {/* Filter Matrix Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Search obligations by required action, obligation code, or text..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
          />
        </form>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <select
              value={documentId}
              onChange={(e) => updateParam('document_id', e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-teal-500"
            >
              <option value="">All Regulatory Documents</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.circular_number || d.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <select
              value={reviewStatus}
              onChange={(e) => updateParam('review_status', e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-teal-500"
            >
              <option value="">All Review Statuses</option>
              <option value="pending">Pending Human Review</option>
              <option value="approved">Approved by Reviewer</option>
              <option value="corrected">Corrected</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          <div>
            <input
              type="text"
              value={entity}
              onChange={(e) => updateParam('entity', e.target.value)}
              placeholder="Filter by Entity (e.g., IBU, FME)..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>
        </div>
      </div>

      {/* Obligations Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px] bg-slate-950/40">
                <th className="py-3 px-4 font-semibold">Obligation Code</th>
                <th className="py-3 px-4 font-semibold">Required Action & Mandatory Text</th>
                <th className="py-3 px-3 font-semibold">Responsible Entity</th>
                <th className="py-3 px-3 font-semibold">Deadline</th>
                <th className="py-3 px-3 font-semibold text-center">Page</th>
                <th className="py-3 px-3 font-semibold text-center">Confidence</th>
                <th className="py-3 px-3 font-semibold">Review Status</th>
                <th className="py-3 px-4 font-semibold text-right">Evidence Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500 mx-auto mb-2"></div>
                    Loading compliance obligations...
                  </td>
                </tr>
              ) : obligations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <Shield className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    No regulatory obligations found matching your filter criteria.
                  </td>
                </tr>
              ) : (
                obligations.map((obl) => (
                  <tr
                    key={obl.id}
                    onClick={() => navigate(`/evidence/${obl.id}`)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-teal-400 whitespace-nowrap">
                      {obl.obligation_code}
                    </td>
                    <td className="py-3.5 px-4 max-w-md">
                      <div className="font-semibold text-slate-200 line-clamp-1 group-hover:text-teal-300 transition-colors">
                        {obl.required_action}
                      </div>
                      <div className="text-[11px] text-slate-400 line-clamp-2 mt-0.5 leading-relaxed">
                        "{obl.obligation_text}"
                      </div>
                    </td>
                    <td className="py-3.5 px-3 whitespace-nowrap font-medium text-slate-300">
                      {obl.responsible_entity || (
                        <span className="text-slate-500 italic text-[11px]">All Regulated Entities</span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      {obl.deadline ? (
                        <span className="inline-flex items-center gap-1 text-amber-300 font-mono text-[11px]">
                          <Clock className="h-3 w-3" /> {obl.deadline}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 text-center font-mono text-slate-300">
                      P.{obl.source_page}
                    </td>
                    <td className="py-3.5 px-3 text-center">
                      <span className="inline-block px-1.5 py-0.5 rounded font-mono text-[10px] font-bold bg-slate-800 text-teal-300 border border-slate-700">
                        {Math.round(obl.confidence_score * 100)}%
                      </span>
                    </td>
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <StatusBadge status={obl.review_status} />
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-teal-400 group-hover:translate-x-1 transition-transform font-medium">
                        Verify <ArrowRight className="h-3.5 w-3.5" />
                      </span>
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
