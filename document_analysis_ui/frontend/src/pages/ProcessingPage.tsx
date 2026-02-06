import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ProgressView } from '../components/progress/ProgressView';
import { useProgress } from '../hooks/useProgress';
import { api } from '../services/api';
import { ArrowLeft } from 'lucide-react';

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
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-gray-600">Loading session status...</p>
      </div>
    );
  }

  if (!sessionId) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Invalid session ID</p>
        <button
          onClick={handleBackToUpload}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Back to Upload
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
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Batch Results
          </button>
        )}

        {(error || isComplete) && (
          <button
            onClick={handleBackToUpload}
            className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors shadow-sm"
          >
            {error ? 'Start Over' : 'Process Another Student'}
          </button>
        )}
      </div>
    </div>
  );
}
