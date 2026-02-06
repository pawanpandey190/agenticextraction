import type { ProcessingMetadata } from '../../services/types';

interface MetadataTabProps {
  data: ProcessingMetadata;
}

export function MetadataTab({ data }: MetadataTabProps) {
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)} seconds`;
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins} min ${secs} sec`;
  };

  return (
    <div className="space-y-6">
      {/* Processing Summary */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Processing Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">
              {data.total_documents_scanned}
            </div>
            <div className="text-sm text-blue-700">Documents Scanned</div>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-green-600">
              {formatDuration(data.processing_time_seconds)}
            </div>
            <div className="text-sm text-green-700">Processing Time</div>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-yellow-600">
              {data.processing_warnings.length}
            </div>
            <div className="text-sm text-yellow-700">Warnings</div>
          </div>
          <div className="bg-red-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-red-600">
              {data.processing_errors.length}
            </div>
            <div className="text-sm text-red-700">Errors</div>
          </div>
        </div>
      </div>

      {/* Documents by Category */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Documents by Category</h3>
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Count
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(data.documents_by_category).map(([category, count]) => (
                <tr key={category}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 capitalize">
                    {category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warnings */}
      {data.processing_warnings.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Warnings</h3>
          <ul className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 space-y-2">
            {data.processing_warnings.map((warning, index) => (
              <li key={index} className="flex items-start space-x-2 text-sm text-yellow-800">
                <svg className="w-5 h-5 text-yellow-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Errors */}
      {data.processing_errors.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Errors</h3>
          <ul className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-2">
            {data.processing_errors.map((error, index) => (
              <li key={index} className="flex items-start space-x-2 text-sm text-red-800">
                <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Success message if no errors or warnings */}
      {data.processing_errors.length === 0 && data.processing_warnings.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center space-x-3">
          <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-green-700">Processing completed without errors or warnings</span>
        </div>
      )}
    </div>
  );
}
