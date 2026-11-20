import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Shield,
  Layers,
  CheckCircle,
  XCircle,
  Edit3,
  MessageSquare,
  Clock,
  Sliders,
  AlertCircle,
  FileText,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { api } from '../services/api';
import { PDFViewer } from '../components/evidence/PDFViewer';
import { StatusBadge } from '../components/common/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const EvidenceViewer = () => {
  const { id } = useParams<{ id: string }>();
  const [evidenceData, setEvidenceData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review Form States
  const [isEditing, setIsEditing] = useState(false);
  const [correctedEntity, setCorrectedEntity] = useState('');
  const [correctedAction, setCorrectedAction] = useState('');
  const [correctedDeadline, setCorrectedDeadline] = useState('');
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewMessage, setReviewMessage] = useState<string | null>(null);

  const { user } = useAuth();
  const navigate = useNavigate();

  const fetchEvidence = async (targetId: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getEvidenceDetails(targetId);
      setEvidenceData(data);
      setCorrectedEntity(data.obligation.responsible_entity || '');
      setCorrectedAction(data.obligation.required_action || '');
      setCorrectedDeadline(data.obligation.deadline || '');
    } catch (err: any) {
      setError(err.message || 'Failed to load evidence details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchEvidence(parseInt(id));
    } else {
      // Default to the first obligation if none selected in URL
      api.getObligations({ limit: 1 }).then((res) => {
        if (res.items.length > 0) {
          navigate(`/evidence/${res.items[0].id}`, { replace: true });
        }
      }).catch(() => {});
    }
  }, [id]);

  const handleReviewAction = async (action: 'approved' | 'rejected' | 'corrected') => {
    if (!evidenceData) return;
    setSubmittingReview(true);
    setReviewMessage(null);

    try {
      const updated = await api.reviewObligation(evidenceData.obligation.id, {
        action,
        responsible_entity: isEditing ? correctedEntity : undefined,
        required_action: isEditing ? correctedAction : undefined,
        deadline: isEditing ? correctedDeadline : undefined,
        comments: reviewComment.trim() || undefined,
      });

      setEvidenceData((prev: any) => ({
        ...prev,
        obligation: {
          ...prev.obligation,
          review_status: updated.review_status,
          responsible_entity: updated.responsible_entity,
          required_action: updated.required_action,
          deadline: updated.deadline,
        },
      }));

      setIsEditing(false);
      setReviewComment('');
      setReviewMessage(`Obligation status successfully marked as '${action}'. Audit log recorded.`);
    } catch (err: any) {
      alert(err.message || 'Failed to submit review decision.');
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-xs">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500 mb-3"></div>
      </div>
    );
  }

  if (error || !evidenceData) {
    return (
      <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center max-w-lg mx-auto">
        <AlertCircle className="h-8 w-8 text-amber-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-white">Evidence Record Unavailable</h3>
        <p className="text-xs text-slate-400 mt-1">{error || 'Please select an obligation from the explorer.'}</p>
        <button
          onClick={() => navigate('/obligations')}
          className="mt-4 px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold rounded-lg text-xs"
        >
          Return to Obligation Explorer
        </button>
      </div>
    );
  }

  const { obligation, document, source_page, evidence_span, reviews, controls } = evidenceData;
  const canReview = user?.role === 'reviewer' || user?.role === 'compliance_officer' || user?.role === 'admin';

  return (
    <div className="space-y-4">
      {/* Top Breadcrumb & Metadata Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/obligations')}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 text-xs flex items-center gap-1"
          >
            <ChevronLeft className="h-4 w-4" /> Back
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold text-teal-400">{obligation.obligation_code}</span>
              <StatusBadge status={obligation.review_status} />
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700">
                Confidence: {Math.round(obligation.confidence_score * 100)}%
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 truncate max-w-xl">
              Source: {document.title} ({document.circular_number || 'IFSCA Circular'})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(`/evidence/${Math.max(obligation.id - 1, 1)}`)}
            className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 text-xs flex items-center gap-1"
            title="Previous Obligation"
          >
            <ChevronLeft className="h-4 w-4" /> Prev
          </button>
          <button
            onClick={() => navigate(`/evidence/${obligation.id + 1}`)}
            className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 text-xs flex items-center gap-1"
            title="Next Obligation"
          >
            Next <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {reviewMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <CheckCircle className="h-4 w-4" /> {reviewMessage}
          </span>
          <button onClick={() => setReviewMessage(null)} className="text-slate-500 hover:text-slate-300">
            &times;
          </button>
        </div>
      )}

      {/* Flagship DUAL-PANEL Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[750px]">
        {/* LEFT PANEL: Original PDF with Visual Bounding Box Highlighting (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col min-h-[650px]">
          <PDFViewer
            documentId={document.id}
            pdfUrl={api.getDocumentPdfUrl(document.id)}
            sourcePage={obligation.source_page}
            exactText={evidence_span ? evidence_span.exact_text : obligation.obligation_text}
            charStart={evidence_span?.char_start}
            charEnd={evidence_span?.char_end}
            pageCount={document.page_count}
            pages={source_page ? [source_page] : []}
          />
        </div>

        {/* RIGHT PANEL: Structured Intelligence & Human Oversight Form (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-4 overflow-y-auto max-h-[800px] pr-1">
          {/* Section 1: Extracted Directive */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Shield className="h-4 w-4 text-teal-400" /> Extracted Compliance Intelligence
              </h3>
              <StatusBadge status={obligation.evidence_status} />
            </div>

            {/* Obligation Text Callout */}
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Full Regulatory Sentence
              </span>
              <p className="mt-1 text-xs text-slate-200 leading-relaxed p-3 bg-slate-950 rounded-lg border border-slate-800 italic">
                "{obligation.obligation_text}"
              </p>
            </div>

            {/* Extracted Fields */}
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Responsible Entity
                </span>
                {isEditing ? (
                  <input
                    type="text"
                    value={correctedEntity}
                    onChange={(e) => setCorrectedEntity(e.target.value)}
                    className="mt-1 w-full bg-slate-950 border border-teal-500 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                ) : (
                  <div className="mt-1 font-semibold text-teal-300">
                    {obligation.responsible_entity || (
                      <span className="text-slate-500 italic">Unspecified (Applies Generally)</span>
                    )}
                  </div>
                )}
              </div>

              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Required Action
                </span>
                {isEditing ? (
                  <textarea
                    rows={2}
                    value={correctedAction}
                    onChange={(e) => setCorrectedAction(e.target.value)}
                    className="mt-1 w-full bg-slate-950 border border-teal-500 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                ) : (
                  <div className="mt-1 text-slate-300 leading-relaxed font-medium">
                    {obligation.required_action}
                  </div>
                )}
              </div>

              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Mandated Deadline
                </span>
                {isEditing ? (
                  <input
                    type="text"
                    value={correctedDeadline}
                    onChange={(e) => setCorrectedDeadline(e.target.value)}
                    placeholder="e.g., within 30 days"
                    className="mt-1 w-full bg-slate-950 border border-teal-500 rounded px-2.5 py-1.5 text-xs text-white"
                  />
                ) : (
                  <div className="mt-1">
                    {obligation.deadline ? (
                      <span className="inline-flex items-center gap-1 text-amber-300 font-mono font-bold">
                        <Clock className="h-3.5 w-3.5" /> {obligation.deadline}
                      </span>
                    ) : (
                      <span className="text-slate-500 italic">No explicit deadline stated</span>
                    )}
                  </div>
                )}
              </div>

              {obligation.conditions && obligation.conditions.length > 0 && (
                <div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Applicable Conditions
                  </span>
                  <ul className="mt-1 list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                    {obligation.conditions.map((c: string, idx: number) => (
                      <li key={idx}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Section 2: Compliance Control Mappings */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="h-4 w-4 text-teal-400" /> Affected Control Taxonomy
            </h3>

            {controls.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No control category mapped yet.</p>
            ) : (
              <div className="space-y-2">
                {controls.map((cm: any) => (
                  <div key={cm.id} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-200">
                        {cm.category_code}: {cm.category_name}
                      </span>
                      <StatusBadge status={cm.review_status} />
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{cm.rationale}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 3: Human Verification Decision Form */}
          {canReview && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle className="h-4 w-4 text-emerald-400" /> Reviewer Decision & Sign-off
                </h3>
                <button
                  type="button"
                  onClick={() => setIsEditing(!isEditing)}
                  className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
                >
                  <Edit3 className="h-3.5 w-3.5" /> {isEditing ? 'Cancel Edit' : 'Correct Fields'}
                </button>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Compliance Audit Comments (Mandatory for rejection or correction)
                </label>
                <textarea
                  rows={2}
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="Record verification notes, legal rationale, or policy basis..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={submittingReview}
                  onClick={() => handleReviewAction('approved')}
                  className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <CheckCircle className="h-3.5 w-3.5" /> Approve
                </button>

                {isEditing ? (
                  <button
                    type="button"
                    disabled={submittingReview}
                    onClick={() => handleReviewAction('corrected')}
                    className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    <Edit3 className="h-3.5 w-3.5" /> Save Corrections
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={submittingReview}
                    onClick={() => handleReviewAction('rejected')}
                    className="flex-1 py-2 bg-rose-700 hover:bg-rose-600 text-white font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    <XCircle className="h-3.5 w-3.5" /> Reject Candidate
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Section 4: Audit & Review History */}
          {reviews && reviews.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <MessageSquare className="h-4 w-4 text-teal-400" /> Historical Review Decisions
              </h3>
              <div className="space-y-2.5">
                {reviews.map((r: any) => (
                  <div key={r.id} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px]">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-300">{r.reviewer_name}</span>
                      <StatusBadge status={r.action} />
                    </div>
                    {r.comments && <p className="text-slate-400 italic">"{r.comments}"</p>}
                    <span className="text-[10px] text-slate-500 mt-1 block font-mono">
                      {new Date(r.created_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
