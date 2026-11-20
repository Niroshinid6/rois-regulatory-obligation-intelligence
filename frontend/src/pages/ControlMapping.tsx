import { useState, useEffect } from 'react';
import { Sliders, Plus, CheckCircle, XCircle, Search, Shield, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { ControlCategory, ObligationControlMapping } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const ControlMapping = () => {
  const [categories, setCategories] = useState<ControlCategory[]>([]);
  const [mappings, setMappings] = useState<ObligationControlMapping[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [loading, setLoading] = useState(true);

  // New Category Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const { user } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [cats, maps] = await Promise.all([
        api.getControlCategories(),
        api.getControlMappings(),
      ]);
      setCategories(cats);
      setMappings(maps);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdateStatus = async (mappingId: number, review_status: 'approved' | 'rejected') => {
    try {
      const updated = await api.updateControlMapping(mappingId, { review_status });
      setMappings((prev) =>
        prev.map((m) => (m.id === mappingId ? { ...m, review_status: updated.review_status } : m))
      );
    } catch (err: any) {
      alert(err.message || 'Failed to update mapping status.');
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await api.createControlCategory({
        code: newCode,
        name: newName,
        description: newDesc,
      });
      setCategories((prev) => [...prev, created]);
      setShowAddModal(false);
      setNewCode('');
      setNewName('');
      setNewDesc('');
    } catch (err: any) {
      alert(err.message || 'Failed to create control category.');
    }
  };

  const filteredMappings = selectedCategory
    ? mappings.filter((m) => m.category_code === selectedCategory)
    : mappings;

  const canManage = user?.role === 'compliance_officer' || user?.role === 'reviewer' || user?.role === 'admin';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Compliance Control Mapping Matrix</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Cross-reference regulatory obligations against the organizational risk and compliance control framework.
          </p>
        </div>

        {canManage && (
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors shadow-sm self-start"
          >
            <Plus className="h-4 w-4" /> Add Control Domain
          </button>
        )}
      </div>

      {/* Control Categories Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <button
          onClick={() => setSelectedCategory('')}
          className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
            selectedCategory === ''
              ? 'bg-teal-500 text-slate-950 font-bold'
              : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800'
          }`}
        >
          All Domains ({mappings.length})
        </button>
        {categories.map((cat) => {
          const count = mappings.filter((m) => m.category_code === cat.code).length;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.code)}
              className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
                selectedCategory === cat.code
                  ? 'bg-teal-500 text-slate-950 font-bold'
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800'
              }`}
            >
              {cat.code}: {cat.name} ({count})
            </button>
          );
        })}
      </div>

      {/* Mappings Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px] bg-slate-950/40">
                <th className="py-3 px-4 font-semibold">Obligation Code</th>
                <th className="py-3 px-4 font-semibold">Mapped Obligation Text</th>
                <th className="py-3 px-3 font-semibold">Control Domain</th>
                <th className="py-3 px-4 font-semibold">Mapping Basis & Rationale</th>
                <th className="py-3 px-3 font-semibold">Method</th>
                <th className="py-3 px-3 font-semibold">Status</th>
                {canManage && <th className="py-3 px-4 font-semibold text-right">Oversight</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500 mx-auto mb-2"></div>
                    Loading control mapping matrix...
                  </td>
                </tr>
              ) : filteredMappings.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <Sliders className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    No control mappings found for the selected category.
                  </td>
                </tr>
              ) : (
                filteredMappings.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-teal-400 whitespace-nowrap">
                      {m.obligation_code || `OBL-${m.obligation_id}`}
                    </td>
                    <td className="py-3 px-4 max-w-sm text-slate-300 line-clamp-2 leading-relaxed">
                      "{m.obligation_text || 'Regulatory obligation requirement'}"
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap font-medium text-white">
                      <span className="font-mono text-teal-300 font-bold">{m.category_code}</span>
                      <div className="text-[10px] text-slate-400">{m.category_name}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px] max-w-xs leading-relaxed">
                      {m.rationale}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                        {m.mapping_method}
                      </span>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <StatusBadge status={m.review_status} />
                    </td>
                    {canManage && (
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {m.review_status !== 'approved' && (
                            <button
                              onClick={() => handleUpdateStatus(m.id, 'approved')}
                              className="p-1.5 rounded hover:bg-emerald-500/20 text-emerald-400"
                              title="Approve Mapping"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </button>
                          )}
                          {m.review_status !== 'rejected' && (
                            <button
                              onClick={() => handleUpdateStatus(m.id, 'rejected')}
                              className="p-1.5 rounded hover:bg-rose-500/20 text-rose-400"
                              title="Reject Mapping"
                            >
                              <XCircle className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Control Category Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders className="h-4 w-4 text-teal-400" /> Add Control Domain
            </h3>

            <form onSubmit={handleCreateCategory} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Domain Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., CAP-01"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Domain Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Capital Adequacy & Solvency"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Scope and compliance description..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold rounded-lg shadow-sm"
                >
                  Create Domain
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
