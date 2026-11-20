import { useState } from 'react';
import { Settings as SettingsIcon, Shield, Sliders, Database, Server, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Settings = () => {
  const [minConfidence, setMinConfidence] = useState('85');
  const [enableOCR, setEnableOCR] = useState(true);
  const [autoMapControls, setAutoMapControls] = useState(true);
  const [saved, setSaved] = useState(false);

  const { user } = useAuth();

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">System Configuration & Governance</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Tune extraction parameters, regulator scopes, and platform telemetry.
        </p>
      </div>

      {saved && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          <span>System configuration updated successfully.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Regulatory Scope */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Shield className="h-4 w-4 text-teal-400" /> Active Regulatory Scope
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Target Regulatory Authority</label>
              <input
                type="text"
                disabled
                value="IFSCA (International Financial Services Centres Authority)"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-300 font-medium cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Jurisdiction Center</label>
              <input
                type="text"
                disabled
                value="GIFT International Financial Services Centre (GIFT City)"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-300 font-medium cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Extraction & NLP Engine */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Sliders className="h-4 w-4 text-teal-400" /> AI Extraction & Anchoring Tuning
          </h3>

          <div className="space-y-4 text-xs">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-slate-300 font-semibold">Minimum Confidence Threshold for Auto-Approval</label>
                <span className="font-mono text-teal-400 font-bold">{minConfidence}%</span>
              </div>
              <input
                type="range"
                min="70"
                max="98"
                value={minConfidence}
                onChange={(e) => setMinConfidence(e.target.value)}
                className="w-full accent-teal-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Extractions scoring below this threshold are automatically routed to the human oversight review queue.
              </p>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
              <div>
                <span className="font-semibold text-slate-300 block">Scanned PDF Detection & OCR Flagging</span>
                <span className="text-[11px] text-slate-500">
                  Transparently flags non-searchable or image-based circulars as 'requires_ocr'
                </span>
              </div>
              <input
                type="checkbox"
                checked={enableOCR}
                onChange={(e) => setEnableOCR(e.target.checked)}
                className="h-4 w-4 accent-teal-500 cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
              <div>
                <span className="font-semibold text-slate-300 block">Automatic Control Taxonomy Suggestions</span>
                <span className="text-[11px] text-slate-500">
                  Maps extracted obligations to compliance control domains (CDD, Reporting, Governance, Risk)
                </span>
              </div>
              <input
                type="checkbox"
                checked={autoMapControls}
                onChange={(e) => setAutoMapControls(e.target.checked)}
                className="h-4 w-4 accent-teal-500 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Section 3: System Environment */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Server className="h-4 w-4 text-teal-400" /> Platform Infrastructure
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block uppercase font-sans">Database Engine</span>
              <span className="text-slate-200 font-bold">SQLAlchemy / SQLite & Postgres</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block uppercase font-sans">PDF Extraction</span>
              <span className="text-teal-400 font-bold">pdfplumber & pypdf 7.1</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block uppercase font-sans">Evaluation Build</span>
              <span className="text-slate-200 font-bold">v1.0.0-GIFT-FutureLab</span>
            </div>
          </div>
        </div>

        {/* Save button */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold rounded-lg text-xs transition-colors shadow-sm"
          >
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
};
