import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DocumentUpload } from '../components/upload/DocumentUpload';
import { useSession } from '../hooks/useSession';
import { Folders } from 'lucide-react';

import { GlassButton } from '../components/common/GlassComponents';
import { motion, AnimatePresence } from 'framer-motion';

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
  const [bankStatementPeriod, setBankStatementPeriod] = useState(3);

  const handleUpload = async (files: File[]) => {
    try {
      let currentSession = session;
      if (!currentSession) {
        currentSession = (await createSession(financialThreshold, bankStatementPeriod)) as any;
      }
      if (currentSession) {
        await uploadFiles(files, currentSession.id);
      }
    } catch (err) { }
  };

  const handleDelete = async (filename: string) => {
    await deleteFile(filename);
  };

  const handleStartAnalysis = async () => {
    if (!session) return;
    try {
      await startProcessing();
      navigate(`/processing/${session.id}`);
    } catch { }
  };

  return (
    <div className="space-y-10">
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex flex-col md:flex-row md:items-end justify-between gap-6"
      >
        <div className="space-y-4">
          <h2 className="text-3xl font-bold tracking-tight text-slate-800 sm:text-4xl">
            New Analysis
          </h2>
          <p className="text-base text-slate-500 font-medium max-w-2xl leading-relaxed">
            Upload documents for automated verification and assessment.
          </p>
        </div>
        <GlassButton
          onClick={() => navigate('/batch-upload')}
          variant="glass"
          icon={<Folders className="w-5 h-5 text-brand-primary" />}
        >
          Batch Students
        </GlassButton>
      </motion.div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-red-50 border border-red-100 rounded-2xl p-5 flex items-start justify-between shadow-sm">
              <div className="flex items-start space-x-3">
                <div className="p-1 rounded-lg bg-red-100/50">
                  <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h5 className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-1">System Error</h5>
                  <span className="text-red-700 font-medium text-sm">{error}</span>
                </div>
              </div>
              <button onClick={clearError} className="text-red-400 hover:text-red-600 transition-colors p-1">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <DocumentUpload
        uploadedFiles={session?.uploaded_files || []}
        onUpload={handleUpload}
        onDelete={handleDelete}
        onStartAnalysis={handleStartAnalysis}
        isLoading={isLoading}
        financialThreshold={financialThreshold}
        onThresholdChange={setFinancialThreshold}
        bankStatementPeriod={bankStatementPeriod}
        onPeriodChange={setBankStatementPeriod}
      />
    </div>
  );
}
