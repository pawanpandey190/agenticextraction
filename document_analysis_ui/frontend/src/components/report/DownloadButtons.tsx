import { api } from '../../services/api';

interface DownloadButtonsProps {
  sessionId: string;
  letter_available?: boolean;
  showLetterDownload?: boolean;
}

export function DownloadButtons({
  sessionId,
  letter_available,
  showLetterDownload = true
}: DownloadButtonsProps) {
  const handleDownloadJson = () => {
    window.open(api.getJsonDownloadUrl(sessionId), '_blank');
  };

  const handleDownloadExcel = () => {
    window.open(api.getExcelDownloadUrl(sessionId), '_blank');
  };

  const handleDownloadLetter = () => {
    const timestamp = new Date().getTime();
    window.open(`${api.getLetterDownloadUrl(sessionId)}?t=${timestamp}`, '_blank');
  };

  return (
    <div className="flex space-x-3">
      {letter_available && showLetterDownload && (
        <button
          onClick={handleDownloadLetter}
          className="inline-flex items-center px-4 py-2 border border-blue-300 rounded-md text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Download Admission Letter (Word)
        </button>
      )}
      <button
        onClick={handleDownloadJson}
        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
      >
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Download JSON
      </button>
      <button
        onClick={handleDownloadExcel}
        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
      >
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Download Excel
      </button>
    </div>
  );
}
