import { useState } from 'react';
import type { AnalysisResult, DocumentMetadata } from '../../services/types';
import { DownloadButtons } from './DownloadButtons';
import { PassportTab } from './PassportTab';
import { FinancialTab } from './FinancialTab';
import { EducationTab } from './EducationTab';
import { CrossValidationTab } from './CrossValidationTab';
import { MetadataTab } from './MetadataTab';
import { DocumentViewer } from './DocumentViewer';
import { FileText, X, Edit, Loader2 } from 'lucide-react';

interface ReportViewProps {
  result: AnalysisResult;
  sessionId: string;
  onNewAnalysis: () => void;
  documents?: DocumentMetadata[];
  letterAvailable?: boolean;
}

type TabId = 'passport' | 'financial' | 'education' | 'crossvalidation' | 'metadata';

interface TabConfig {
  id: TabId;
  label: string;
  hasData: boolean;
}

export function ReportView({
  result,
  sessionId,
  onNewAnalysis,
  documents = [],
  letterAvailable
}: ReportViewProps) {
  const [activeTab, setActiveTab] = useState<TabId>('passport');
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
    // Pre-fill with existing data
    const p = result.passport;
    const existingName = p ? `${p.first_name || ''} ${p.last_name || ''}`.trim() : '';
    setManualName(existingName);

    // Default to today's date in "January 6th, 2026" format
    setManualDate(formatOrdinalDate(new Date()));

    setIsManualModalOpen(true);
  };

  const handleGenerateManual = async () => {
    setIsGenerating(true);
    try {
      const { api } = await import('../../services/api');
      await api.generateManualLetter(sessionId, manualName, manualDate);

      // Trigger download with cache-buster
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

  const tabs: TabConfig[] = [
    { id: 'passport', label: 'Passport', hasData: result.passport !== null },
    { id: 'financial', label: 'Financial', hasData: result.financial !== null },
    { id: 'education', label: 'Education', hasData: result.education !== null },
    { id: 'crossvalidation', label: 'Cross-Validation', hasData: result.cross_validation !== null },
    { id: 'metadata', label: 'Metadata', hasData: true },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'passport':
        return <PassportTab data={result.passport} />;
      case 'financial':
        return <FinancialTab data={result.financial} />;
      case 'education':
        return <EducationTab data={result.education} />;
      case 'crossvalidation':
        return <CrossValidationTab data={result.cross_validation} />;
      case 'metadata':
        return <MetadataTab data={result.metadata} />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analysis Report</h2>
          <p className="text-gray-500 text-sm mt-1">
            {result.metadata.total_documents_scanned} documents analyzed
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Show Documents Button */}
          {documents.length > 0 && (
            <button
              onClick={() => setShowDocuments(!showDocuments)}
              className={`inline-flex items-center px-4 py-2 rounded-md transition-colors ${showDocuments
                ? 'bg-gray-600 text-white hover:bg-gray-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              {showDocuments ? (
                <>
                  <X className="w-4 h-4 mr-2" />
                  Hide Documents
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  View Documents ({documents.length})
                </>
              )}
            </button>
          )}
          <DownloadButtons
            sessionId={sessionId}
            letter_available={letterAvailable}
            showLetterDownload={isHighAccuracy}
          />

          <button
            onClick={handleOpenManualModal}
            className={`inline-flex items-center px-4 py-2 rounded-md transition-colors border font-medium ${isHighAccuracy
              ? 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-200'
              : 'bg-amber-100 text-amber-700 hover:bg-amber-200 border-amber-200'
              }`}
            title={isHighAccuracy ? "Edit student name or date for the letter." : "Accuracy is low. Click to manually edit name and date."}
          >
            <Edit className="w-4 h-4 mr-2" />
            {isHighAccuracy ? 'Edit Letter' : 'Manual Letter'}
          </button>

          <button
            onClick={onNewAnalysis}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Analysis
          </button>
        </div>
      </div>

      {/* Split-pane layout */}
      <div className={`grid gap-6 ${showDocuments ? 'lg:grid-cols-2' : 'grid-cols-1'}`}>
        {/* Results panel */}
        <div className="space-y-6">
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 overflow-x-auto">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="flex items-center space-x-2">
                    <span>{tab.label}</span>
                    {!tab.hasData && tab.id !== 'metadata' && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-500">
                        N/A
                      </span>
                    )}
                  </span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="py-4">
            {renderTabContent()}
          </div>
        </div>

        {/* Document viewer panel */}
        {showDocuments && (
          <div className="lg:sticky lg:top-6 h-[800px]">
            <DocumentViewer
              sessionId={sessionId}
              documents={documents}
            />
          </div>
        )}
      </div>

      {/* Manual Letter Modal */}
      {isManualModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-amber-50">
              <h3 className="text-lg font-semibold text-amber-900 flex items-center">
                <Edit className="w-5 h-5 mr-2" />
                Edit Letter Details
              </h3>
              <button onClick={() => setIsManualModalOpen(false)} className="text-amber-700 hover:text-amber-900">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-600 mb-4">
                Passport accuracy is low ({passportAccuracy}%). Please verify and correct the student details before generating the letter.
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Student Name</label>
                <input
                  type="text"
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
                  placeholder="e.g. Pawan Pandey"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Letter Date</label>
                <input
                  type="text"
                  value={manualDate}
                  onChange={(e) => setManualDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
                  placeholder="DD/MM/YYYY"
                />
                <p className="text-[10px] text-gray-400 mt-1">Format: DD/MM/YYYY (e.g., 06/02/2026)</p>
              </div>
            </div>

            <div className="px-6 py-4 bg-gray-50 flex justify-end gap-3">
              <button
                onClick={() => setIsManualModalOpen(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                disabled={isGenerating}
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateManual}
                disabled={isGenerating || !manualName}
                className="flex items-center px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm font-medium"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate & Download'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
