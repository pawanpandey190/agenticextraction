import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { Session, UploadResponse } from '../services/types';

interface UseSessionReturn {
  session: Session | null;
  isLoading: boolean;
  error: string | null;
  createSession: (financialThreshold?: number, bankStatementPeriod?: number) => Promise<Session>;
  loadSession: (sessionId: string) => Promise<void>;
  uploadFiles: (files: File[], sessionId?: string) => Promise<UploadResponse>;
  deleteFile: (filename: string) => Promise<void>;
  startProcessing: () => Promise<void>;
  clearError: () => void;
}

export function useSession(): UseSessionReturn {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createSession = useCallback(async (financialThreshold: number = 15000, bankStatementPeriod: number = 3) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.createSession(financialThreshold, bankStatementPeriod);
      const newSession = await api.getSession(response.session_id);
      setSession(newSession);
      return newSession;
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to create session';
      setError(message);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const loadedSession = await api.getSession(sessionId);
      setSession(loadedSession);
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to load session';
      setError(message);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadFiles = useCallback(async (files: File[], sessionId?: string) => {
    const targetSessionId = sessionId || session?.id;
    if (!targetSessionId) {
      throw new Error('No active session');
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.uploadDocuments(targetSessionId, files);
      // Refresh session to get updated file list
      const updatedSession = await api.getSession(targetSessionId);
      setSession(updatedSession);
      return response;
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to upload files';
      setError(message);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  const deleteFile = useCallback(async (filename: string) => {
    if (!session) {
      throw new Error('No active session');
    }
    setIsLoading(true);
    setError(null);
    try {
      await api.deleteDocument(session.id, filename);
      // Refresh session
      const updatedSession = await api.getSession(session.id);
      setSession(updatedSession);
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to delete file';
      setError(message);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  const startProcessing = useCallback(async () => {
    if (!session) {
      throw new Error('No active session');
    }
    setError(null);
    try {
      await api.startProcessing(session.id);
      // Refresh session to get updated status
      const updatedSession = await api.getSession(session.id);
      setSession(updatedSession);
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to start processing';
      setError(message);
      throw e;
    }
  }, [session]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    session,
    isLoading,
    error,
    createSession,
    loadSession,
    uploadFiles,
    deleteFile,
    startProcessing,
    clearError,
  };
}
