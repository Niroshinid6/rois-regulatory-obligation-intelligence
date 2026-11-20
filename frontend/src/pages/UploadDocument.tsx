import { useState, useRef, ChangeEvent, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, Shield } from 'lucide-react';
import { api } from '../services/api';

export const UploadDocument = () => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [circularNumber, setCircularNumber] = useState('');
  const [regulator, setRegulator] = useState('IFSCA');
  const [publicationDate, setPublicationDate] = useState('');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [category, setCategory] = useState('Circular');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<any | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Please upload an authentic PDF file (.pdf).');
        return;
      }
      setFile(selected);
      setError(null);

      // Auto-populate title if empty
      if (!title) {
        const cleanName = selected.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' ');
        setTitle(cleanName);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Please upload an authentic PDF file (.pdf).');
        return;
      }
      setFile(selected);
      setError(null);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '));
      }
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF document to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (circularNumber) formData.append('circular_number', circularNumber);
    formData.append('regulator', regulator);
    if (publicationDate) formData.append('publication_date', publicationDate);
    if (effectiveDate) formData.append('effective_date', effectiveDate);
    formData.append('category', category);
    if (description) formData.append('description', description);

    try {
      const createdDoc = await api.uploadDocument(formData);
      setSuccess(createdDoc);
    } catch (err: any) {
      setError(err.message || 'Upload and processing failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">Upload Regulatory Document</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Ingest authentic IFSCA regulatory circulars for automatic layout parsing, coordinate evidence anchoring, and obligation extraction.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-start gap-2.5">
          <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-semibold">Document Validation Error</div>
            <div className="mt-0.5 text-slate-300">{error}</div>
          </div>
        </div>
      )}

      {success ? (
        <div className="p-6 rounded-2xl bg-slate-900 border border-teal-500/40 text-center space-y-4 shadow-xl">
          <div className="h-12 w-12 rounded-full bg-teal-500/20 border border-teal-500/40 text-teal-400 flex items-center justify-center mx-auto">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Document Processed Successfully!</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Extracted <strong className="text-teal-400">{success.obligation_count}</strong> compliance obligations across{' '}
              <strong className="text-slate-200">{success.page_count} pages</strong> with character coordinate evidence spans.
            </p>
          </div>

          <div className="pt-2 flex items-center justify-center gap-3">
            <button
              onClick={() => navigate(`/obligations?document_id=${success.id}`)}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1.5 transition-colors shadow-sm"
            >
              Explore Extracted Obligations <ArrowRight className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => {
                setSuccess(null);
                setFile(null);
                setTitle('');
                setCircularNumber('');
              }}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg text-xs border border-slate-700"
            >
              Upload Another
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-sm">
          {/* Dropzone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              file
                ? 'border-teal-500 bg-teal-500/5'
                : 'border-slate-800 hover:border-slate-700 bg-slate-950/40'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="application/pdf"
              className="hidden"
            />
            {file ? (
              <div className="flex flex-col items-center">
                <FileText className="h-10 w-10 text-teal-400 mb-2" />
                <span className="text-sm font-semibold text-white">{file.name}</span>
                <span className="text-xs text-slate-400 mt-1">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB — PDF Ready for Extraction
                </span>
                <span className="mt-3 text-[11px] text-teal-400 underline font-medium">Click to select a different file</span>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <UploadCloud className="h-10 w-10 text-slate-500 mb-2" />
                <span className="text-sm font-medium text-slate-200">
                  Drag and drop authentic regulatory circular PDF here, or <span className="text-teal-400 font-semibold">browse</span>
                </span>
                <span className="text-xs text-slate-500 mt-1">
                  Maximum file size: 25MB • Strict PDF binary validation
                </span>
              </div>
            )}
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Document / Circular Title <span className="text-teal-400">*</span>
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., IFSCA Guidelines on Capital Adequacy for Broker Dealers, 2024"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Circular / Reference Number
              </label>
              <input
                type="text"
                value={circularNumber}
                onChange={(e) => setCircularNumber(e.target.value)}
                placeholder="e.g., IFSCA/2024-25/GN/CIR-003"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Issuing Regulatory Authority
              </label>
              <input
                type="text"
                required
                value={regulator}
                onChange={(e) => setRegulator(e.target.value)}
                placeholder="IFSCA"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Publication Date
              </label>
              <input
                type="date"
                value={publicationDate}
                onChange={(e) => setPublicationDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Document Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
              >
                <option value="Circular">Circular</option>
                <option value="Guidelines">Guidelines</option>
                <option value="Regulations">Regulations</option>
                <option value="Framework">Framework</option>
                <option value="Master Direction">Master Direction</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Description / Regulatory Scope Notes (Optional)
              </label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Specify regulatory applicability, targeted market participants, or amendments..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          {/* Submit */}
          <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => navigate('/documents')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-2 transition-colors disabled:opacity-50 shadow-sm"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-slate-950"></div>
                  Extracting Layout & Obligations...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4" />
                  Process & Anchor Obligations
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
