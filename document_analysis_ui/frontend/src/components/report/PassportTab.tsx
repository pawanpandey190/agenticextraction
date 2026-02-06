import type { PassportDetails } from '../../services/types';

interface PassportTabProps {
  data: PassportDetails | null;
}

interface FieldProps {
  label: string;
  value: string | number | null | undefined;
}

function Field({ label, value }: FieldProps) {
  return (
    <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
        {value ?? <span className="text-gray-400 italic">Not available</span>}
      </dd>
    </div>
  );
}

export function PassportTab({ data }: PassportTabProps) {
  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="mt-2">No passport data available</p>
        <p className="text-sm">No passport documents were found in the uploaded files</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Personal Information */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Personal Information</h3>
        <div className="bg-white border rounded-lg divide-y divide-gray-200 px-4">
          <Field label="First Name" value={data.first_name} />
          <Field label="Last Name" value={data.last_name} />
          <Field label="Date of Birth" value={data.date_of_birth} />
        </div>
      </div>

      {/* Passport Details */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Passport Details</h3>
        <div className="bg-white border rounded-lg divide-y divide-gray-200 px-4">
          <Field label="Passport Number" value={data.passport_number} />
          <Field label="Issuing Country" value={data.issuing_country} />
          <Field label="Issue Date" value={data.issue_date} />
          <Field label="Expiry Date" value={data.expiry_date} />
        </div>
      </div>

      {/* MRZ Data */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">MRZ Data</h3>
        <div className="bg-gray-50 border rounded-lg p-4 font-mono text-sm">
          <div className="mb-2">{data.mrz_line1 || <span className="text-gray-400">Line 1 not available</span>}</div>
          <div>{data.mrz_line2 || <span className="text-gray-400">Line 2 not available</span>}</div>
        </div>
      </div>

      {/* Accuracy Score */}
      {data.accuracy_score !== null && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Validation</h3>
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">Accuracy Score:</span>
            <span className={`
              inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
              ${data.accuracy_score >= 80 ? 'bg-green-100 text-green-800' :
                data.accuracy_score >= 50 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'}
            `}>
              {data.accuracy_score.toFixed(1)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
