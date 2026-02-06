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
      <div className="text-center py-8">
        <p className="text-red-600">Invalid session ID</p>
        <button
          onClick={handleNewAnalysis}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Start New Analysis
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <svg className="animate-spin h-10 w-10 text-blue-500 mx-auto" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-3 text-gray-500">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
          <svg className="w-12 h-12 text-red-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-3 text-lg font-medium text-red-800">Failed to Load Results</h3>
          <p className="mt-2 text-red-600">{error}</p>
          <button
            onClick={handleNewAnalysis}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Start New Analysis
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
      onNewAnalysis={handleNewAnalysis}
      documents={documents}
      letterAvailable={letterAvailable}
    />
  );
}
