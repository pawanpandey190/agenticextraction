import { useEffect, useState } from 'react';
import { ProgressBar } from './ProgressBar';
import { StageIndicator } from './StageIndicator';
import type { ProgressEvent } from '../../services/types';

interface ProgressViewProps {
  progress: ProgressEvent | null;
  isProcessing: boolean;
  isComplete: boolean;
  error: string | null;
  onComplete: () => void;
  sessionId?: string;  // For cancel functionality
  onCancel?: () => void;  // Callback after cancellation
}

export function ProgressView({
  progress,
  isProcessing,
  isComplete,
  error,
  onComplete,
  sessionId,
  onCancel,
}: ProgressViewProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  // Elapsed time counter
  useEffect(() => {
    if (!isProcessing) return;

    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [isProcessing]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleCancelClick = () => {
    setShowCancelConfirm(true);
  };

  const handleCancelConfirm = async () => {
    if (!sessionId) return;

    setIsCancelling(true);
    setShowCancelConfirm(false);

    try {
      const { api } = await import('../../services/api');
      await api.cancelProcessing(sessionId);
      if (onCancel) {
        onCancel();
      }
    } catch (err) {
      console.error('Failed to cancel processing:', err);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleCancelDismiss = () => {
    setShowCancelConfirm(false);
  };

  if (error) {
    return (
      <div className="bg-white border border-red-100 rounded-2xl p-8 shadow-sm flex flex-col items-center text-center">
        <div className="w-16 h-16 bg-red-50 rounded-xl flex items-center justify-center mb-6 border border-red-100">
          <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-slate-800 tracking-tight mb-2">Analysis Interrupted</h3>
        <p className="text-red-500 font-medium text-sm leading-relaxed">{error}</p>
      </div>
    );
  }

  if (isComplete) {
    return (
      <div className="bg-white border border-brand-secondary/20 rounded-2xl p-8 shadow-sm">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-6">
            <div className="w-16 h-16 bg-brand-secondary/10 rounded-xl flex items-center justify-center border border-brand-secondary/20">
              <svg className="w-8 h-8 text-brand-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 tracking-tight">Analysis Complete</h3>
              <p className="text-brand-secondary font-semibold text-xs uppercase tracking-wider mt-1">
                Completed in {formatTime(elapsedTime)}
              </p>
            </div>
          </div>
          <button
            onClick={onComplete}
            className="px-8 py-3 bg-brand-primary text-white rounded-xl font-bold uppercase text-xs tracking-wider hover:bg-brand-primary/90 transition-all shadow-md shadow-brand-primary/10"
          >
            View Results
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="text-center space-y-3">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Document <span className="text-brand-primary">Processing</span></h2>
        <p className="text-slate-400 font-medium text-sm">
          {progress?.message || 'Starting analysis...'}
        </p>

        {/* Document progress */}
        {progress?.total_documents && progress.total_documents > 0 && (
          <div className="inline-flex items-center px-4 py-1.5 bg-brand-primary/5 rounded-full border border-brand-primary/10">
            <p className="text-xs font-semibold text-brand-primary uppercase tracking-wider">
              {progress.current_document
                ? `Analyzing: ${progress.current_document}`
                : `Document ${(progress.processed_documents || 0) + 1} of ${progress.total_documents}`
              }
            </p>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <ProgressBar percentage={progress?.percentage || 0} />

      {/* Elapsed time and Cancel button */}
      <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider px-2">
        <span className="text-slate-400">
          Time: <span className="text-slate-800">{formatTime(elapsedTime)}</span>
        </span>

        {sessionId && !isCancelling && (
          <button
            onClick={handleCancelClick}
            className="text-red-400 hover:text-red-600 transition-colors font-semibold"
          >
            Cancel
          </button>
        )}

        {isCancelling && (
          <span className="text-red-500 animate-pulse font-semibold">Cancelling...</span>
        )}
      </div>

      {/* Stage indicator */}
      <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-8 px-2">Stages</h3>
        <StageIndicator
          currentStageIndex={progress?.stage_index || 0}
          isComplete={isComplete}
        />
      </div>

      {/* Sub-agent info */}
      {progress?.sub_agent && (
        <div className="text-center text-xs font-semibold text-brand-primary uppercase tracking-widest px-4 py-6 opacity-40">
          Agent: {progress.sub_agent}
        </div>
      )}

      {/* Cancel confirmation dialog */}
      {showCancelConfirm && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-xl animate-in zoom-in duration-300">
            <h3 className="text-xl font-bold text-slate-800 tracking-tight mb-4 text-center">Cancel Process?</h3>
            <p className="text-sm text-slate-500 font-medium mb-8 leading-relaxed text-center">
              Are you sure you want to cancel the current analysis?
            </p>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={handleCancelDismiss}
                className="px-6 py-3 bg-slate-50 text-slate-700 rounded-xl font-bold uppercase text-xs tracking-wider hover:bg-slate-100 transition-all"
              >
                Go Back
              </button>
              <button
                onClick={handleCancelConfirm}
                className="px-6 py-3 bg-red-500 text-white rounded-xl font-bold uppercase text-xs tracking-wider hover:bg-red-600 transition-all shadow-md shadow-red-500/10"
              >
                Yes, Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
