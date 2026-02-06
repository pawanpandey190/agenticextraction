import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DocumentUpload } from '../components/upload/DocumentUpload';
import { useSession } from '../hooks/useSession';
import { Folders } from 'lucide-react';

export function UploadPage() {
  const navigate = useNavigate();
  const {
    session,
    isLoading,
    error,
    createSession,
    uploadFiles,
    deleteFile,
    startProcessing,
    clearError,
  } = useSession();

  const [financialThreshold, setFinancialThreshold] = useState(15000);

  // Create session on mount
  useEffect(() => {
    if (!session) {
      createSession(financialThreshold).catch(() => {
        // Error is handled in the hook
      });
    }
  }, []);

  const handleUpload = async (files: File[]) => {
    await uploadFiles(files);
  };

  const handleDelete = async (filename: string) => {
    await deleteFile(filename);
  };

  const handleStartAnalysis = async () => {
    if (!session) return;
    try {
      await startProcessing();
      navigate(`/processing/${session.id}`);
    } catch {
      // Error is handled in the hook
    }
  };

  if (!session && isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <svg className="animate-spin h-10 w-10 text-blue-500 mx-auto" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-3 text-gray-500">Creating session...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Document Analysis</h1>
            <p className="mt-2 text-gray-600">
              Upload your documents to analyze passports, financial records, and education credentials.
            </p>
          </div>
          <button
            onClick={() => navigate('/batch-upload')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Folders className="w-5 h-5" />
            Batch Upload
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-red-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-700">{error}</span>
          </div>
          <button onClick={clearError} className="text-red-400 hover:text-red-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {session && (
        <DocumentUpload
          uploadedFiles={session.uploaded_files}
          onUpload={handleUpload}
          onDelete={handleDelete}
          onStartAnalysis={handleStartAnalysis}
          isLoading={isLoading}
          financialThreshold={financialThreshold}
          onThresholdChange={setFinancialThreshold}
        />
      )}
    </div>
  );
}
