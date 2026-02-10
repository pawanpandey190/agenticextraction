import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { AnalysisResult, DocumentMetadata } from '../../services/types';
import { DownloadButtons } from './DownloadButtons';
import { PassportTab } from './PassportTab';
import { FinancialTab } from './FinancialTab';
import { EducationTab } from './EducationTab';
import { CrossValidationTab } from './CrossValidationTab';
import { SummaryTab } from './SummaryTab';
import { MetadataTab } from './MetadataTab';
import { DocumentViewer } from './DocumentViewer';
import { GlassCard, GlassButton } from '../common/GlassComponents';
import { FileText, X, Edit, ChevronRight, Activity, ShieldCheck, PieChart, CheckCircle2 } from 'lucide-react';

interface ReportViewProps {
  result: AnalysisResult;
  sessionId: string;
  documents?: DocumentMetadata[];
  letterAvailable?: boolean;
}

type TabId = 'summary' | 'passport' | 'financial' | 'education' | 'crossvalidation' | 'metadata';

export function ReportView({
  result,
  sessionId,
  documents = [],
  letterAvailable
}: ReportViewProps) {
  const [activeTab, setActiveTab] = useState<TabId>('summary');
  const [showDocuments, setShowDocuments] = useState(false);
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [manualName, setManualName] = useState('');
  const [manualDate, setManualDate] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const passportAccuracy = result.passport?.accuracy_score ?? 0;
  const isHighAccuracy = passportAccuracy >= 70;

  const getOrdinalSuffix = (day: number) => {
    if (day > 3 && day < 21) return 'th';
    switch (day % 10) {
      case 1: return 'st';
      case 2: return 'nd';
      case 3: return 'rd';
      default: return 'th';
    }
  };

  const formatOrdinalDate = (date: Date) => {
    const month = date.toLocaleString('default', { month: 'long' });
    const day = date.getDate();
    const year = date.getFullYear();
    return `${month} ${day}${getOrdinalSuffix(day)}, ${year}`;
  };

  const handleOpenManualModal = () => {
    const p = result.passport;
    const existingName = p ? `${p.first_name || ''} ${p.last_name || ''}`.trim() : '';
    setManualName(existingName);
    setManualDate(formatOrdinalDate(new Date()));
    setIsManualModalOpen(true);
  };

  const handleGenerateManual = async () => {
    setIsGenerating(true);
    try {
      const { api } = await import('../../services/api');
      await api.generateManualLetter(sessionId, manualName, manualDate);
      const timestamp = new Date().getTime();
      const downloadUrl = `${api.getLetterDownloadUrl(sessionId)}?t=${timestamp}`;
      window.open(downloadUrl, '_blank');
      setIsManualModalOpen(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to generate letter');
    } finally {
      setIsGenerating(false);
    }
  };

  const tabs = [
    { id: 'summary', label: 'Overview', icon: <Activity className="w-4 h-4" /> },
    { id: 'passport', label: 'Identity', icon: <ShieldCheck className="w-4 h-4" /> },
    { id: 'financial', label: 'Financials', icon: <PieChart className="w-4 h-4" /> },
    { id: 'education', label: 'Academic', icon: <FileText className="w-4 h-4" /> },
    { id: 'crossvalidation', label: 'Validation', icon: <CheckCircle2 className="w-4 h-4" /> },
  ] as const;

  const renderTabContent = () => {
    return (
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {activeTab === 'summary' && <SummaryTab data={result} />}
        {activeTab === 'passport' && <PassportTab data={result.passport} />}
        {activeTab === 'financial' && <FinancialTab data={result.financial} />}
        {activeTab === 'education' && <EducationTab data={result.education} />}
        {activeTab === 'crossvalidation' && <CrossValidationTab data={result.cross_validation} />}
        {activeTab === 'metadata' && <MetadataTab data={result.metadata} />}
      </motion.div>
    );
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Dynamic Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-1"
        >
          <div className="flex items-center gap-2 text-brand-primary mb-2">
            <span className="px-2 py-0.5 rounded-full bg-brand-primary/10 text-xs font-semibold uppercase tracking-wider border border-brand-primary/20">
              Audit Complete
            </span>
            <span className="text-slate-500">•</span>
            <span className="text-xs text-slate-400 font-medium">Session ID: {sessionId.slice(0, 8)}...</span>
          </div>
          <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Analysis Report</h2>
        </motion.div>

        <div className="flex flex-wrap items-center gap-3">
          <GlassButton
            onClick={() => setShowDocuments(!showDocuments)}
            variant="glass"
            icon={showDocuments ? <X className="w-4 h-4" /> : <FileText className="w-4 h-4 text-brand-primary" />}
          >
            {showDocuments ? 'Close Viewer' : `View Sources (${documents.length})`}
          </GlassButton>

          <DownloadButtons
            sessionId={sessionId}
            letter_available={letterAvailable}
            showLetterDownload={isHighAccuracy}
          />

        </div>
      </div>

      {/* Bento-Style Metrics Grid */}
      {!showDocuments && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <GlassCard className="flex flex-col items-center justify-center p-8 text-center border-slate-200 bg-white shadow-sm transition-all hover:bg-slate-50/50">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-6">Identity Check</p>
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90">
                <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-100" />
                <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent"
                  strokeDasharray={364} strokeDashoffset={364 - (364 * passportAccuracy) / 100}
                  className="text-brand-primary transition-all duration-1000 ease-out" strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-slate-800">{passportAccuracy}%</span>
                <span className="text-xs font-semibold text-brand-primary uppercase">Confidence</span>
              </div>
            </div>
          </GlassCard>

          <GlassCard className={`p-8 border-slate-200 bg-white shadow-sm transition-all hover:bg-slate-50/50 ${result.financial?.worthiness_status === 'FAIL' ? 'border-red-200 bg-red-50' : ''}`}>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-6 text-center">Financial Status</p>
            <div className="flex flex-col items-center gap-4">
              <div className={`p-4 rounded-2xl ${result.financial?.worthiness_status === 'PASS' ? 'bg-brand-secondary/10 text-brand-secondary' : 'bg-red-100 text-red-500'}`}>
                {result.financial?.worthiness_status === 'PASS' ? (
                  <CheckCircle2 className="w-12 h-12" />
                ) : (
                  <ShieldCheck className="w-12 h-12" />
                )}
              </div>
              <div className="text-center">
                <h4 className="text-xl font-bold text-slate-800">
                  {result.financial?.french_equivalence || 'Pending Analysis'}
                </h4>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-1">€{(result.financial?.amount_eur || 0).toLocaleString()} Solvent</p>
              </div>
            </div>
          </GlassCard>

          <GlassCard className={`p-8 border-slate-200 bg-white shadow-sm transition-all hover:bg-slate-50/50 ${result.education?.validation_status === 'FAIL' ? 'border-red-200 bg-red-50' : ''}`}>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-6 text-center">Academic Status</p>
            <div className="flex flex-col items-center gap-4">
              <div className={`p-4 rounded-2xl ${result.education?.validation_status === 'PASS' ? 'bg-brand-primary/10 text-brand-primary' : 'bg-amber-100 text-amber-600'}`}>
                <Activity className="w-12 h-12" />
              </div>
              <div className="text-center">
                <h4 className="text-xl font-bold text-slate-800">
                  {result.education?.french_equivalence || 'Pending Equivalence'}
                </h4>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-1">{(result.education?.french_equivalent_grade_0_20 ?? 0).toFixed(2)}/20 French Scale</p>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-8 flex flex-col justify-between transition-transform hover:scale-[1.01]">
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">System Actions</p>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <div className="w-1 h-8 bg-brand-primary rounded-full"></div>
                  <div>
                    <h5 className="text-xs font-bold text-slate-800 uppercase tracking-tight">Manual Review</h5>
                    <p className="text-xs text-slate-500 font-medium leading-tight mt-1">
                      {isHighAccuracy ? 'Eligible for auto-generation' : 'Verification required'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-start pt-4">
              <button
                onClick={handleOpenManualModal}
                className="text-xs font-bold text-brand-primary hover:text-brand-primary/80 transition-colors flex items-center gap-2 group whitespace-nowrap uppercase tracking-wider"
              >
                Edit Letter <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Main Results Container */}
      <div className={`grid gap-8 ${showDocuments ? 'lg:grid-cols-2' : 'grid-cols-1'}`}>
        <div className="space-y-6">
          {/* Custom Glass Tabs */}
          <div className="flex p-1 gap-1 bg-slate-100 rounded-2xl border border-slate-200 overflow-x-auto custom-scrollbar no-scrollbar">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-6 py-2 rounded-xl font-bold text-xs uppercase tracking-wider transition-all whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'bg-white text-brand-primary shadow-sm border border-slate-200'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-white/50'
                  }
                `}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          <div className="min-h-[400px]">
            {renderTabContent()}
          </div>
        </div>

        {/* Immersive Document Viewer */}
        <AnimatePresence>
          {showDocuments && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="lg:sticky lg:top-24 h-[80vh] rounded-[2rem] overflow-hidden border border-slate-200 shadow-xl bg-white"
            >
              <DocumentViewer
                sessionId={sessionId}
                documents={documents}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Manual Letter Modal */}
      {isManualModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4">
          <GlassCard className="w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200 border-slate-200 shadow-2xl p-0">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-white">
              <h3 className="text-lg font-bold text-slate-800 tracking-tight flex items-center">
                <Edit className="w-5 h-5 mr-3 text-brand-primary" />
                Correction Interface
              </h3>
              <button onClick={() => setIsManualModalOpen(false)} className="text-slate-400 hover:text-slate-900 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-sm text-slate-400 mb-4">
                Passport accuracy is low ({passportAccuracy}%). Please verify and correct the student details before generating the letter.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 ml-1">Verified Student Name</label>
                <input
                  type="text"
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary outline-none transition-all placeholder:text-slate-400 font-medium"
                  placeholder="e.g. Pawan Pandey"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 ml-1">Document Issuance Date</label>
                <input
                  type="text"
                  value={manualDate}
                  onChange={(e) => setManualDate(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary outline-none transition-all placeholder:text-slate-400 font-medium"
                  placeholder="DD/MM/YYYY"
                />
                <p className="text-[10px] font-semibold text-slate-400 mt-2 ml-1 italic">Expected Format: DD/MM/YYYY</p>
              </div>
            </div>

            <div className="px-6 py-4 bg-slate-50/50 flex justify-end gap-3 border-t border-slate-100">
              <button
                onClick={() => setIsManualModalOpen(false)}
                className="px-6 py-2 text-slate-400 hover:text-slate-900 transition-colors font-bold text-xs uppercase tracking-wider"
                disabled={isGenerating}
              >
                Cancel
              </button>
              <GlassButton
                onClick={handleGenerateManual}
                isLoading={isGenerating}
                disabled={!manualName}
                variant="primary"
                size="sm"
              >
                Generate Final Letter
              </GlassButton>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
