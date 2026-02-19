import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2, Download, X } from 'lucide-react';
import type { DocumentMetadata } from '../../services/types';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker - use unpkg.com CDN (cdnjs returns 404 for this version)
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@5.4.296/build/pdf.worker.min.mjs`;

interface DocumentViewerProps {
    sessionId: string;
    documents: DocumentMetadata[];
    baseUrl?: string;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
    sessionId,
    documents,
    baseUrl = 'http://localhost:8000',
}) => {
    const [selectedDoc, setSelectedDoc] = useState<string>(documents[0]?.filename || '');
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [scale, setScale] = useState<number>(1.0);
    const [error, setError] = useState<string | null>(null);
    const [isFullScreen, setIsFullScreen] = useState(false);

    const selectedDocument = documents.find(d => d.filename === selectedDoc);
    const isPDF = selectedDocument?.type === 'application/pdf';
    const isImage = selectedDocument?.type?.startsWith('image/');

    const documentUrl = selectedDoc
        ? `${baseUrl}/api/sessions/${sessionId}/documents/${encodeURIComponent(selectedDoc)}/view`
        : '';

    const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
        setNumPages(numPages);
        setPageNumber(1);
        setError(null);
    };

    const onDocumentLoadError = (error: Error) => {
        console.error('Error loading document:', error);
        setError('Failed to load document. Please try again.');
    };

    const handleZoomIn = () => setScale(prev => Math.min(prev + 0.2, 5.0));
    const handleZoomOut = () => setScale(prev => Math.max(prev - 0.2, 0.2));
    const handleResetScale = () => setScale(1.0);

    const handlePrevPage = () => setPageNumber(prev => Math.max(prev - 1, 1));
    const handleNextPage = () => setPageNumber(prev => Math.min(prev + 1, numPages));

    const toggleFullScreen = () => {
        setIsFullScreen(!isFullScreen);
        if (!isFullScreen) {
            setScale(1.2);
        } else {
            setScale(1.0);
        }
    };

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isFullScreen) {
                toggleFullScreen();
            }
        };

        if (isFullScreen) {
            window.addEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'hidden';
        }

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'unset';
        };
    }, [isFullScreen]);

    if (documents.length === 0) {
        return (
            <div className="flex items-center justify-center h-full bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                <div className="text-center text-slate-400">
                    <svg className="mx-auto h-12 w-12 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="mt-2 font-bold uppercase tracking-widest text-[10px]">No documents available</p>
                </div>
            </div>
        );
    }

    const ViewerContent = ({ inModal = false }: { inModal?: boolean }) => (
        <div className={inModal ? "flex-1 overflow-auto p-4 md:p-12" : "flex-1 overflow-auto p-4 bg-slate-100"}>
            {!error && isPDF && (
                <div className="flex justify-center min-h-full items-start">
                    <Document
                        file={documentUrl}
                        onLoadSuccess={onDocumentLoadSuccess}
                        onLoadError={onDocumentLoadError}
                        loading={
                            <div className="flex items-center justify-center p-8">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-primary"></div>
                            </div>
                        }
                    >
                        {Array.from(new Array(numPages), (_, index) => (
                            <Page
                                key={`page_${index + 1}`}
                                pageNumber={index + 1}
                                scale={scale}
                                className="mb-4 shadow-lg"
                                loading={
                                    <div className="flex items-center justify-center p-4">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary"></div>
                                    </div>
                                }
                                renderTextLayer={true}
                                renderAnnotationLayer={true}
                            />
                        ))}
                    </Document>
                </div>
            )}

            {!error && isImage && (
                <div className="flex justify-center min-h-full items-start">
                    <img
                        src={documentUrl}
                        alt={selectedDoc}
                        className="max-w-full rounded-xl shadow-2xl transition-transform duration-200 pointer-events-none"
                        style={{ transform: `scale(${scale})`, transformOrigin: 'top center' }}
                        onError={() => setError('Failed to load image')}
                    />
                </div>
            )}

            {!error && !isPDF && !isImage && (
                <div className="text-center text-slate-500 p-8">
                    <p className="font-bold uppercase tracking-widest text-[10px] text-slate-400 mb-4">Preview not available</p>
                    <a
                        href={documentUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-primary font-bold text-xs uppercase hover:underline inline-flex items-center gap-2"
                    >
                        <Download className="w-3.5 h-3.5" /> Download to view
                    </a>
                </div>
            )}
        </div>
    );

    return (
        <div className="flex flex-col h-full bg-white rounded-[2rem] border border-slate-200 overflow-hidden">
            {/* Header with document selector */}
            <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50 gap-3">
                <div className="flex-1">
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">
                        Active Source
                    </label>
                    <select
                        value={selectedDoc}
                        onChange={(e) => {
                            setSelectedDoc(e.target.value);
                            setPageNumber(1);
                            handleResetScale();
                            setError(null);
                        }}
                        className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl font-bold text-xs text-slate-700 focus:outline-none focus:ring-4 focus:ring-brand-primary/10 focus:border-brand-primary transition-all shadow-sm"
                    >
                        {documents.map((doc) => (
                            <option key={doc.filename} value={doc.filename}>
                                {doc.filename} ({(doc.size / 1024).toFixed(1)} KB)
                            </option>
                        ))}
                    </select>
                </div>

                {/* Download button */}
                <div className="flex items-end pb-0.5">
                    <a
                        href={documentUrl}
                        download={selectedDoc}
                        className="inline-flex items-center px-4 py-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-all font-bold text-xs uppercase tracking-wider shadow-lg active:scale-95"
                        title="Download document"
                    >
                        <Download className="w-3.5 h-3.5 mr-2" />
                        Save
                    </a>
                </div>
            </div>

            {/* Toolbar - Now visible for both PDF and Images */}
            {(isPDF || isImage) && (
                <div className="flex flex-wrap items-center justify-between p-3 border-b border-slate-100 bg-white">
                    {/* Page navigation (PDF only) */}
                    <div className="flex items-center gap-1">
                        {isPDF && (
                            <>
                                <button
                                    onClick={handlePrevPage}
                                    disabled={pageNumber <= 1}
                                    className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 disabled:opacity-20 transition-colors"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest min-w-[80px] text-center">
                                    {pageNumber} / {numPages}
                                </span>
                                <button
                                    onClick={handleNextPage}
                                    disabled={pageNumber >= numPages}
                                    className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 disabled:opacity-20 transition-colors"
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </>
                        )}
                    </div>

                    {/* Zoom controls (For both PDF and Image) */}
                    <div className="flex items-center gap-1">
                        <button
                            onClick={handleZoomOut}
                            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
                            title="Zoom out"
                        >
                            <ZoomOut className="w-4 h-4" />
                        </button>
                        <button
                            onClick={handleResetScale}
                            className="px-2 py-1 rounded-lg hover:bg-slate-100 text-[10px] font-black text-slate-400 uppercase tracking-widest transition-colors"
                            title="Reset zoom"
                        >
                            {Math.round(scale * 100)}%
                        </button>
                        <button
                            onClick={handleZoomIn}
                            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
                            title="Zoom in"
                        >
                            <ZoomIn className="w-4 h-4" />
                        </button>
                        <div className="w-px h-4 bg-slate-200 mx-2" />
                        <button
                            onClick={toggleFullScreen}
                            className="p-2 rounded-lg bg-brand-primary/10 text-brand-primary hover:bg-brand-primary/20 transition-all active:scale-90"
                            title="View Fullscreen"
                        >
                            <Maximize2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            {/* Main Viewer Area */}
            <ViewerContent />

            {/* Immersive Fullscreen Modal - Rendered via Portal to escape parent clips */}
            {isFullScreen && createPortal(
                <div className="fixed inset-0 z-[9999] bg-slate-900/95 backdrop-blur-xl flex flex-col overflow-hidden animate-in fade-in duration-300">
                    <div className="flex items-center justify-between p-6 bg-slate-900/50 border-b border-white/10 shadow-2xl">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-brand-primary uppercase tracking-[0.3em] mb-1">Fullscreen Inspector</span>
                            <h3 className="text-white font-bold text-sm tracking-tight">{selectedDoc}</h3>
                        </div>

                        <div className="flex items-center gap-4">
                            {/* In-modal zoom controls */}
                            <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-2xl border border-white/10">
                                <button onClick={handleZoomOut} className="p-1 hover:text-brand-primary text-white transition-colors"><ZoomOut className="w-4 h-4" /></button>
                                <span className="text-[10px] font-black text-white uppercase tracking-widest min-w-[40px] text-center">{Math.round(scale * 100)}%</span>
                                <button onClick={handleZoomIn} className="p-1 hover:text-brand-primary text-white transition-colors"><ZoomIn className="w-4 h-4" /></button>
                            </div>

                            <button
                                onClick={toggleFullScreen}
                                className="p-3 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white rounded-2xl transition-all duration-300 shadow-2xl group border border-red-500/20"
                                title="Close Inspector"
                            >
                                <X className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-auto bg-transparent custom-scrollbar flex flex-col">
                        <ViewerContent inModal={true} />
                    </div>

                    <div className="p-4 bg-slate-900/50 border-t border-white/5 text-center">
                        <p className="text-[10px] font-black text-white/30 uppercase tracking-[0.5em]">Press ESC or click close to exit inspector</p>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
};
