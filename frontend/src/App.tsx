import { Shield, Sparkles, BookOpen, Layers } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-center items-center p-6">
      <div className="max-w-2xl w-full bg-slate-800 border border-slate-700 rounded-xl p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 rounded-lg bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400">
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              ROIS <span className="text-xs bg-teal-500/10 text-teal-300 border border-teal-500/30 px-2 py-0.5 rounded font-mono">v1.0.0-phaseA</span>
            </h1>
            <p className="text-sm text-slate-400">Regulatory Obligation Intelligence System</p>
          </div>
        </div>

        <p className="text-slate-300 mb-6 text-sm leading-relaxed border-l-2 border-teal-500 pl-4 py-1">
          "Every compliance obligation, traced to the exact sentence that created it."
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
          <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-700/60 flex items-start gap-3">
            <Sparkles className="h-5 w-5 text-teal-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-white">IFSCA Regulatory Focus</h3>
              <p className="text-xs text-slate-400 mt-1">Ground truth extraction with character-level coordinate anchoring.</p>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-700/60 flex items-start gap-3">
            <BookOpen className="h-5 w-5 text-teal-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-white">Evidence-First RegTech</h3>
              <p className="text-xs text-slate-400 mt-1">Transparent modal classification and human oversight.</p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-slate-700 text-xs text-slate-400">
          <span>GIFT FutureLab Evaluation Prototype</span>
          <span className="flex items-center gap-1 text-teal-400">
            <Layers className="h-3.5 w-3.5" /> Ready for Phase B
          </span>
        </div>
      </div>
    </div>
  );
}
