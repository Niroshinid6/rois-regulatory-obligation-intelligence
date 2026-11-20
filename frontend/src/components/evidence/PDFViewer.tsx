import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Download, Eye, FileText } from 'lucide-react';
import { DocumentPage } from '../../types';

interface PDFViewerProps {
  documentId: number;
  pdfUrl: string;
  sourcePage: number;
  exactText: string;
  charStart?: number;
  charEnd?: number;
  pageCount: number;
  pages: DocumentPage[];
}

export const PDFViewer = ({
  documentId,
  pdfUrl,
  sourcePage,
  exactText,
  charStart,
  charEnd,
  pageCount,
  pages,
}: PDFViewerProps) => {
  const [currentPage, setCurrentPage] = useState(sourcePage || 1);
  const [viewMode, setViewMode] = useState<'pdf' | 'text'>('pdf');
  const [pdfObjectUrl, setPdfObjectUrl] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let objectUrl: string | null = null;
    const token = localStorage.getItem('rois_token');

    if (!token) {
      setPdfError('Your session is unavailable. Sign in again to open this PDF.');
      setPdfObjectUrl(null);
      return () => controller.abort();
    }

    setPdfError(null);
    setPdfObjectUrl(null);

    fetch(pdfUrl, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Could not load the original PDF (HTTP ${response.status}).`);
        }
        if (!response.headers.get('content-type')?.includes('application/pdf')) {
          throw new Error('The document endpoint did not return a PDF.');
        }
        return response.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setPdfObjectUrl(objectUrl);
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setPdfError(error instanceof Error ? error.message : 'Could not load the original PDF.');
        }
      });

    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [pdfUrl]);

  useEffect(() => {
    setCurrentPage(sourcePage || 1);
  }, [sourcePage, documentId]);

  const activePageData = pages.find((page) => page.page_number === currentPage);
  const totalPages = pageCount || Math.max(...pages.map((page) => page.page_number), 0);
  const evidenceOffsetIsValid =
    currentPage === sourcePage &&
    activePageData !== undefined &&
    exactText.length > 0 &&
    Number.isInteger(charStart) &&
    Number.isInteger(charEnd) &&
    charStart !== undefined &&
    charEnd !== undefined &&
    charStart >= 0 &&
    charEnd > charStart &&
    activePageData.extracted_text.slice(charStart, charEnd) === exactText;

  const renderPageText = () => {
    if (!activePageData) {
      return <p className="text-sm text-slate-400">Extracted text for this page is unavailable.</p>;
    }

    if (!evidenceOffsetIsValid || charStart === undefined || charEnd === undefined) {
      return <pre className="whitespace-pre-wrap text-xs leading-relaxed text-slate-800">{activePageData.extracted_text}</pre>;
    }

    return (
      <pre className="whitespace-pre-wrap text-xs leading-relaxed text-slate-800">
        {activePageData.extracted_text.slice(0, charStart)}
        <mark className="bg-teal-200 text-slate-950">
          {activePageData.extracted_text.slice(charStart, charEnd)}
        </mark>
        {activePageData.extracted_text.slice(charEnd)}
      </pre>
    );
  };

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-950 shadow-lg">
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-4 py-2.5 text-xs">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-medium text-slate-300">
            <FileText className="h-4 w-4 text-teal-400" />
            Source Document
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((page) => Math.max(page - 1, 1))}
              disabled={currentPage <= 1}
              className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white disabled:opacity-40"
              title="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="px-1.5 font-mono text-slate-300">
              Page {currentPage} of {totalPages || '—'}
            </span>
            <button
              onClick={() => setCurrentPage((page) => Math.min(page + 1, totalPages || page))}
              disabled={!totalPages || currentPage >= totalPages}
              className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white disabled:opacity-40"
              title="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('pdf')}
            className={`rounded px-2 py-1 ${viewMode === 'pdf' ? 'bg-teal-500 font-semibold text-slate-950' : 'text-slate-400 hover:text-white'}`}
          >
            Original PDF
          </button>
          <button
            onClick={() => setViewMode('text')}
            className={`flex items-center gap-1 rounded px-2 py-1 ${viewMode === 'text' ? 'bg-teal-500 font-semibold text-slate-950' : 'text-slate-400 hover:text-white'}`}
          >
            <Eye className="h-3.5 w-3.5" /> Extracted text
          </button>
          <a
            href={pdfObjectUrl ?? undefined}
            download={`rois-document-${documentId}.pdf`}
            aria-disabled={!pdfObjectUrl}
            className="flex items-center gap-1 rounded-lg border border-slate-700/60 bg-slate-800 p-1.5 text-slate-300 hover:bg-slate-700 hover:text-white aria-disabled:pointer-events-none aria-disabled:opacity-40"
            title="Download original PDF"
          >
            <Download className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>

      <div className="min-h-[600px] flex-1 overflow-auto bg-slate-950/70 p-4">
        {viewMode === 'pdf' ? (
          pdfObjectUrl ? (
            <iframe
              src={`${pdfObjectUrl}#page=${currentPage}`}
              title="Original regulatory PDF"
              className="h-full min-h-[650px] w-full rounded-lg border border-slate-800 bg-slate-900"
            />
          ) : (
            <div className="flex h-full min-h-[600px] items-center justify-center p-8 text-center text-sm text-rose-300">
              {pdfError || 'Loading original PDF…'}
            </div>
          )
        ) : (
          <div className="mx-auto min-h-[600px] max-w-3xl rounded-sm border border-slate-300 bg-white p-8 shadow-2xl">
            <div className="mb-4 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Extracted page text — page {currentPage}
            </div>
            {renderPageText()}
            {currentPage === sourcePage && exactText && (
              <p className="mt-4 border-l-4 border-teal-600 bg-teal-50 p-3 text-xs text-teal-950">
                {evidenceOffsetIsValid
                  ? 'The marked passage matches the stored source offsets.'
                  : 'The stored offsets do not match this page text; no evidence highlight is shown.'}
              </p>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-slate-800 bg-slate-900 px-4 py-2 text-[11px] text-slate-400">
        <span>
          {currentPage === sourcePage
            ? evidenceOffsetIsValid
              ? 'Evidence text verified against page offsets'
              : 'No text highlight: evidence alignment is unverified'
            : `Viewing page ${currentPage}`}
        </span>
        <span>{pdfError ? 'Original PDF unavailable' : 'Original PDF loaded with session authorization'}</span>
      </div>
    </div>
  );
};
