import type { CrossValidation } from '../../services/types';

interface CrossValidationTabProps {
  data: CrossValidation | null;
}

interface MatchIndicatorProps {
  label: string;
  isMatch: boolean | null;
  score?: number | null;
}

function MatchIndicator({ label, isMatch, score }: MatchIndicatorProps) {
  if (isMatch === null) {
    return (
      <div className="flex items-center justify-between py-4 border-b border-gray-200">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-500">
          Not available
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between py-4 border-b border-gray-200">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <div className="flex items-center space-x-3">
        {score !== null && score !== undefined && (
          <span className="text-sm text-gray-500">{(score * 100).toFixed(1)}% match</span>
        )}
        <span className={`
          inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
          ${isMatch ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
        `}>
          {isMatch ? (
            <>
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Match
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Mismatch
            </>
          )}
        </span>
      </div>
    </div>
  );
}

export function CrossValidationTab({ data }: CrossValidationTabProps) {
  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <p className="mt-2">No cross-validation data available</p>
        <p className="text-sm">Cross-validation requires multiple document types</p>
      </div>
    );
  }

  const allMatch = data.name_match === true && data.dob_match === true;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className={`
        rounded-lg p-4 flex items-center space-x-3
        ${allMatch ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}
      `}>
        {allMatch ? (
          <>
            <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <div>
              <h3 className="text-lg font-medium text-green-800">All Data Consistent</h3>
              <p className="text-sm text-green-600">Personal information matches across all documents</p>
            </div>
          </>
        ) : (
          <>
            <svg className="w-8 h-8 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h3 className="text-lg font-medium text-yellow-800">Discrepancies Found</h3>
              <p className="text-sm text-yellow-600">Some information does not match across documents</p>
            </div>
          </>
        )}
      </div>

      {/* Match Details */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Validation Results</h3>
        <div className="bg-white border rounded-lg px-4">
          <MatchIndicator
            label="Name Match"
            isMatch={data.name_match}
            score={data.name_match_score}
          />
          <MatchIndicator
            label="Date of Birth Match"
            isMatch={data.dob_match}
          />
        </div>
      </div>

      {/* Remarks */}
      {data.remarks && data.remarks.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Remarks</h3>
          <ul className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
            {data.remarks.map((remark, index) => (
              <li key={index} className="flex items-start space-x-2 text-sm text-gray-700">
                <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{remark}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
