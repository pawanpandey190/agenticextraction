import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ProgressView } from '../components/progress/ProgressView';
import { useProgress } from '../hooks/useProgress';
import { api } from '../services/api';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';

export function ProcessingPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { progress, isProcessing, isComplete, error, restoreProgress } = useProgress();
  const [session, setSession] = useState<any>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);

  useEffect(() => {
    if (sessionId) {
      setIsLoadingSession(true);
      api.getSession(sessionId)
        .then((s) => {
          setSession(s);
          restoreProgress(s);
          setIsLoadingSession(false);
        })
        .catch(err => {
          console.error("Failed to fetch session:", err);
          setIsLoadingSession(false);
        });
    }
  }, [sessionId, restoreProgress]);

  const handleComplete = () => {
    if (sessionId) {
      navigate(`/report/${sessionId}`);
    }
  };

  const handleBackToUpload = () => {
    navigate('/');
  };

  const handleBackToBatch = () => {
    if (session?.batch_id) {
      navigate(`/batch/${session.batch_id}`);
    } else {
      navigate('/');
    }
  };

  if (isLoadingSession) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <Loader2 className="animate-spin h-10 w-10 text-brand-primary mb-6 opacity-30" />
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Loading status...</p>
      </div>
    );
  }

  if (!sessionId) {
    return (
      <div className="text-center py-20 bg-white border border-red-100 rounded-2xl shadow-sm">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-slate-800 tracking-tight mb-2">Session Not Found</h3>
        <p className="text-red-600 font-medium text-sm mb-8 px-8">The requested analysis session could not be located.</p>
        <button
          onClick={handleBackToUpload}
          className="px-8 py-3 bg-slate-900 text-white rounded-xl font-bold uppercase text-xs tracking-wider hover:bg-slate-800 transition-all shadow-md shadow-slate-900/10"
        >
          Return to Hub
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <ProgressView
        progress={progress}
        isProcessing={isProcessing}
        isComplete={isComplete}
        error={error}
        onComplete={handleComplete}
        sessionId={sessionId}
        onCancel={handleBackToBatch}
      />

      <div className="mt-8 flex flex-col items-center gap-4">
        {session?.batch_id && (
          <button
            onClick={handleBackToBatch}
            className="flex items-center gap-2 text-xs font-semibold text-brand-primary uppercase tracking-wider hover:text-brand-primary/80 transition-all group"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-1 transition-transform" />
            Back to Batch
          </button>
        )}

        {(error || isComplete) && (
          <button
            onClick={handleBackToUpload}
            className="px-8 py-4 bg-white border border-slate-200 text-slate-700 rounded-xl font-bold uppercase text-xs tracking-wider hover:bg-slate-50 transition-all shadow-sm"
          >
            {error ? 'Try Again' : 'New Analysis'}
          </button>
        )}
      </div>
    </div>
  );
}
