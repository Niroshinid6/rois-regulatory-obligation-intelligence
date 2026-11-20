import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, UploadCloud, Search, Download, Trash2, Eye, RefreshCw, AlertCircle, Layers } from 'lucide-react';
import { api } from '../services/api';
import { DocumentItem } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const Documents = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { user } = useAuth();
  const navigate = useNavigate();

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDocuments({
        search: searchTerm || undefined,
        status: statusFilter || undefined,
      });
      setDocuments(data.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents repository.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDocuments();
  };

  const handleDelete = async (id: number, title: string) => {
    if (!window.confirm(`Are you sure you want to delete '${title}'? This will remove all associated extracted obligations and evidence spans.`)) {
      return;
    }

    setDeletingId(id);
    try {
      await api.deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err: any) {
      alert(err.message || 'Failed to delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  const canDelete = user?.role === 'admin' || user?.role === 'compliance_officer';

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Regulatory Document Repository</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage authentic regulatory circulars, extraction telemetry, and source integrity.
          </p>
        </div>

        <button
          onClick={() => navigate('/upload')}
          className="px-3.5 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors shadow-sm self-start"
        >
          <UploadCloud className="h-4 w-4" /> Upload New Circular
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row items-center gap-3">
        <form onSubmit={handleSearch} className="flex-1 relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search circulars by title or reference number..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
          />
        </form>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-teal-500"
          >
            <option value="">All Statuses</option>
            <option value="processed">Processed</option>
            <option value="requires_ocr">Requires OCR</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>

          <button
            onClick={fetchDocuments}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Documents Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px] bg-slate-950/40">
                <th className="py-3 px-4 font-semibold">Document Title</th>
                <th className="py-3 px-3 font-semibold">Reference</th>
                <th className="py-3 px-3 font-semibold">Regulator</th>
                <th className="py-3 px-3 font-semibold">Date</th>
                <th className="py-3 px-3 font-semibold text-center">Pages</th>
                <th className="py-3 px-3 font-semibold text-center">Obligations</th>
                <th className="py-3 px-3 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500 mx-auto mb-2"></div>
                    Loading document repository...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <FileText className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    No regulatory documents found matching your criteria.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-medium text-white max-w-xs truncate">
                      <div className="truncate font-semibold text-slate-200">{doc.title}</div>
                      <div className="text-[10px] text-slate-500 truncate">{doc.category}</div>
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-teal-400">
                      {doc.circular_number || 'N/A'}
                    </td>
                    <td className="py-3 px-3 font-medium text-slate-300">
                      {doc.regulator}
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {doc.publication_date || 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-center text-slate-300 font-mono">
                      {doc.page_count}
                    </td>
                    <td className="py-3 px-3 text-center font-bold text-teal-400 font-mono">
                      {doc.obligation_count || 0}
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => navigate(`/obligations?document_id=${doc.id}`)}
                          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-teal-400"
                          title="Explore Obligations"
                        >
                          <Layers className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => api.downloadDocument(doc.id).catch((err) => alert(err.message))}
                          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
                          title="Download Original PDF"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        {canDelete && (
                          <button
                            onClick={() => handleDelete(doc.id, doc.title)}
                            disabled={deletingId === doc.id}
                            className="p-1.5 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 disabled:opacity-40"
                            title="Delete Document"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
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
