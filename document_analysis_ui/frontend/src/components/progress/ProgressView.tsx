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
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-lg font-medium text-red-800">Processing Failed</h3>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (isComplete) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 className="text-lg font-medium text-green-800">Analysis Complete</h3>
              <p className="text-sm text-green-600">
                Completed in {formatTime(elapsedTime)}
              </p>
            </div>
          </div>
          <button
            onClick={onComplete}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            View Results
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900">Analyzing Documents</h2>
        <p className="text-gray-500 mt-1">
          {progress?.message || 'Starting...'}
        </p>

        {/* Document progress */}
        {progress?.total_documents && progress.total_documents > 0 && (
          <p className="text-sm text-blue-600 mt-2">
            {progress.current_document
              ? `Processing: ${progress.current_document}`
              : `Document ${(progress.processed_documents || 0) + 1} of ${progress.total_documents}`
            }
          </p>
        )}
      </div>

      {/* Progress bar */}
      <ProgressBar percentage={progress?.percentage || 0} />

      {/* Elapsed time and Cancel button */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-500">
          Elapsed time: {formatTime(elapsedTime)}
        </span>

        {sessionId && !isCancelling && (
          <button
            onClick={handleCancelClick}
            className="px-3 py-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
          >
            Cancel Processing
          </button>
        )}

        {isCancelling && (
          <span className="text-gray-500">Cancelling...</span>
        )}
      </div>

      {/* Stage indicator */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Processing Stages</h3>
        <StageIndicator
          currentStageIndex={progress?.stage_index || 0}
          isComplete={isComplete}
        />
      </div>

      {/* Sub-agent info */}
      {progress?.sub_agent && (
        <div className="text-center text-sm text-blue-600">
          Processing with {progress.sub_agent} agent...
        </div>
      )}

      {/* Cancel confirmation dialog */}
      {showCancelConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Cancel Processing?</h3>
            <p className="text-sm text-gray-600 mb-4">
              Are you sure you want to cancel? This will stop the analysis and you'll need to start over.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={handleCancelDismiss}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              >
                Continue Processing
              </button>
              <button
                onClick={handleCancelConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
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
