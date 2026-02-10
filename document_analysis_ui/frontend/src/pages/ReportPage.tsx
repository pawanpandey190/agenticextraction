import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ReportView } from '../components/report/ReportView';
import { api } from '../services/api';
import type { AnalysisResult, DocumentMetadata } from '../services/types';

export function ReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [letterAvailable, setLetterAvailable] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const fetchData = async () => {
      try {
        // Fetch result, documents, and session in parallel
        const [resultData, documentsData, sessionData] = await Promise.all([
          api.getResult(sessionId),
          api.listSessionDocuments(sessionId).catch(() => ({ documents: [] })),
          api.getSession(sessionId),
        ]);

        setResult(resultData);
        setDocuments(documentsData.documents || []);
        setLetterAvailable(sessionData.letter_available || false);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load results');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [sessionId]);

  const handleNewAnalysis = () => {
    navigate('/');
  };

  if (!sessionId) {
    return (
      <div className="text-center py-20 bg-white border border-red-100 rounded-2xl shadow-sm">
        <div className="w-16 h-16 bg-red-50 rounded-xl flex items-center justify-center mb-6 border border-red-100 mx-auto">
          <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-slate-800 tracking-tight mb-2">Report Not Found</h3>
        <p className="text-red-600 font-medium text-sm mb-8 px-8">The requested analysis result could not be located.</p>
        <button
          onClick={handleNewAnalysis}
          className="px-8 py-3 bg-slate-900 text-white rounded-xl font-bold uppercase text-xs tracking-wider hover:bg-slate-800 transition-all shadow-md shadow-slate-900/10"
        >
          Return to Hub
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="relative">
          <svg className="animate-spin h-12 w-12 text-brand-primary opacity-20" fill="none" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-2 h-2 bg-brand-primary rounded-full animate-pulse" />
          </div>
        </div>
        <p className="mt-6 text-xs font-semibold text-slate-400 uppercase tracking-wider">Loading results...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-white border border-red-100 rounded-2xl p-12 max-w-xl mx-auto shadow-sm">
          <div className="w-20 h-20 bg-red-50 rounded-2xl flex items-center justify-center mb-8 border border-red-100 mx-auto">
            <svg className="w-10 h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-slate-800 tracking-tight mb-4">Pipeline Error</h3>
          <p className="text-slate-500 font-medium text-sm leading-relaxed mb-10 px-6">{error}</p>
          <button
            onClick={handleNewAnalysis}
            className="px-10 py-4 bg-slate-900 text-white rounded-xl font-bold uppercase text-xs tracking-wider hover:bg-slate-800 transition-all shadow-md shadow-slate-900/10"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">No results available</p>
        <button
          onClick={handleNewAnalysis}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Start New Analysis
        </button>
      </div>
    );
  }

  return (
    <ReportView
      result={result}
      sessionId={sessionId}
      documents={documents}
      letterAvailable={letterAvailable}
    />
  );
}
