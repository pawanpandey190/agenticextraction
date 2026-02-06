import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';
import type { ProgressEvent } from '../services/types';

interface UseProgressReturn {
  progress: ProgressEvent | null;
  isProcessing: boolean;
  isComplete: boolean;
  error: string | null;
  startProgress: (sessionId: string) => void;
  restoreProgress: (session: any) => void;
  reset: () => void;
}

const STAGE_NAMES = [
  'DocumentScanner',
  'DocumentClassifier',
  'AgentDispatcher',
  'ResultNormalizer',
  'CrossValidator',
  'OutputGenerator',
];

export function useProgress(): UseProgressReturn {
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const startProgress = useCallback((sessionId: string) => {
    // Clean up any existing subscription
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
    }

    setIsProcessing(true);
    setIsComplete(false);
    setError(null);
    setProgress({
      stage_name: STAGE_NAMES[0],
      stage_index: 0,
      total_stages: 6,
      message: 'Starting processing...',
      percentage: 0,
      sub_agent: null,
      completed: false,
      error: null,
    });

    unsubscribeRef.current = api.subscribeToProgress(
      sessionId,
      (event) => {
        setProgress(event);
      },
      (err) => {
        setError(err.message);
        setIsProcessing(false);
      },
      () => {
        setIsComplete(true);
        setIsProcessing(false);
      }
    );
  }, []);

  // Track processing state in a ref to keep restoreProgress stable
  const isProcessingRef = useRef(isProcessing);
  useEffect(() => {
    isProcessingRef.current = isProcessing;
  }, [isProcessing]);

  const restoreProgress = useCallback((session: any) => {
    if (!session) return;

    if (session.status === 'completed') {
      setIsComplete(true);
      setIsProcessing(false);
      setProgress({
        stage_name: STAGE_NAMES[STAGE_NAMES.length - 1],
        stage_index: STAGE_NAMES.length - 1,
        total_stages: STAGE_NAMES.length,
        message: 'Processing complete',
        percentage: 100,
        completed: true,
        error: null,
        sub_agent: null,
      });
    } else if (session.status === 'failed') {
      setError(session.error_message || 'Processing failed');
      setIsProcessing(false);
      setIsComplete(false);
      setProgress({
        stage_name: 'Error',
        stage_index: 0,
        total_stages: STAGE_NAMES.length,
        message: session.error_message || 'Processing failed',
        percentage: 0,
        completed: false,
        error: session.error_message || 'Processing failed',
        sub_agent: null,
      });
    } else if (session.status === 'processing') {
      // Initialize with backend progress before starting SSE
      setProgress({
        stage_name: 'Processing...',
        stage_index: Math.min(Math.floor(session.progress_percentage / (100 / STAGE_NAMES.length)), STAGE_NAMES.length - 1),
        total_stages: STAGE_NAMES.length,
        message: session.current_document ? `Processing ${session.current_document}...` : 'Resuming processing...',
        percentage: session.progress_percentage || 0,
        completed: false,
        error: null,
        sub_agent: null,
      });

      if (!isProcessingRef.current) {
        startProgress(session.id);
      }
    }
  }, [startProgress]); // Removed isProcessing dependency

  const reset = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }
    setProgress(null);
    setIsProcessing(false);
    setIsComplete(false);
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, []);

  return {
    progress,
    isProcessing,
    isComplete,
    error,
    startProgress,
    restoreProgress,
    reset,
  };
}

export { STAGE_NAMES };
