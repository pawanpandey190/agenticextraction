import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2, Download } from 'lucide-react';
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

    const handleZoomIn = () => setScale(prev => Math.min(prev + 0.2, 3.0));
    const handleZoomOut = () => setScale(prev => Math.max(prev - 0.2, 0.5));
    const handleFitToWidth = () => setScale(1.0);

    const handlePrevPage = () => setPageNumber(prev => Math.max(prev - 1, 1));
    const handleNextPage = () => setPageNumber(prev => Math.min(prev + 1, numPages));

    if (documents.length === 0) {
        return (
            <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-center text-gray-500">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="mt-2">No documents available</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200">
            {/* Header with document selector */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50 gap-3">
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Select Document
                    </label>
                    <select
                        value={selectedDoc}
                        onChange={(e) => {
                            setSelectedDoc(e.target.value);
                            setPageNumber(1);
                            setScale(1.0);
                            setError(null);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {documents.map((doc) => (
                            <option key={doc.filename} value={doc.filename}>
                                {doc.filename} ({(doc.size / 1024).toFixed(1)} KB)
                            </option>
                        ))}
                    </select>
                </div>

                {/* Download button */}
                <div className="flex items-end pb-1">
                    <a
                        href={documentUrl}
                        download={selectedDoc}
                        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        title="Download document"
                    >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                    </a>
                </div>
            </div>

            {/* Toolbar */}
            {isPDF && (
                <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50">
                    {/* Page navigation */}
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={handlePrevPage}
                            disabled={pageNumber <= 1}
                            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Previous page"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </button>
                        <span className="text-sm text-gray-700">
                            Page {pageNumber} of {numPages}
                        </span>
                        <button
                            onClick={handleNextPage}
                            disabled={pageNumber >= numPages}
                            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Next page"
                        >
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Zoom controls */}
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={handleZoomOut}
                            className="p-1 rounded hover:bg-gray-200"
                            title="Zoom out"
                        >
                            <ZoomOut className="w-5 h-5" />
                        </button>
                        <span className="text-sm text-gray-700 min-w-[60px] text-center">
                            {Math.round(scale * 100)}%
                        </span>
                        <button
                            onClick={handleZoomIn}
                            className="p-1 rounded hover:bg-gray-200"
                            title="Zoom in"
                        >
                            <ZoomIn className="w-5 h-5" />
                        </button>
                        <button
                            onClick={handleFitToWidth}
                            className="p-1 rounded hover:bg-gray-200"
                            title="Fit to width"
                        >
                            <Maximize2 className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            )}

            {/* Document viewer */}
            <div className="flex-1 overflow-auto p-4 bg-gray-100">
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                        {error}
                    </div>
                )}

                {!error && isPDF && (
                    <div className="flex justify-center">
                        <Document
                            file={documentUrl}
                            onLoadSuccess={onDocumentLoadSuccess}
                            onLoadError={onDocumentLoadError}
                            loading={
                                <div className="flex items-center justify-center p-8">
                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                                </div>
                            }
                        >
                            <Page
                                pageNumber={pageNumber}
                                scale={scale}
                                loading={
                                    <div className="flex items-center justify-center p-8">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                    </div>
                                }
                                renderTextLayer={true}
                                renderAnnotationLayer={true}
                            />
                        </Document>
                    </div>
                )}

                {!error && isImage && (
                    <div className="flex justify-center">
                        <img
                            src={documentUrl}
                            alt={selectedDoc}
                            className="max-w-full h-auto rounded shadow-lg"
                            style={{ transform: `scale(${scale})`, transformOrigin: 'top center' }}
                            onError={() => setError('Failed to load image')}
                        />
                    </div>
                )}

                {!error && !isPDF && !isImage && (
                    <div className="text-center text-gray-500 p-8">
                        <p>Preview not available for this file type</p>
                        <a
                            href={documentUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline mt-2 inline-block"
                        >
                            Download to view
                        </a>
                    </div>
                )}
            </div>
        </div>
    );
};
