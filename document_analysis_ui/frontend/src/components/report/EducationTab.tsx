import type { EducationSummary } from '../../services/types';

interface EducationTabProps {
  data: EducationSummary | null;
}

interface FieldProps {
  label: string;
  value: string | number | null | undefined;
  highlight?: boolean;
}

function Field({ label, value, highlight = false }: FieldProps) {
  return (
    <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className={`mt-1 text-sm sm:mt-0 sm:col-span-2 ${highlight ? 'font-semibold text-blue-700' : 'text-gray-900'}`}>
        {value ?? <span className="text-gray-400 italic">Not available</span>}
      </dd>
    </div>
  );
}

export function EducationTab({ data }: EducationTabProps) {
  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path d="M12 14l9-5-9-5-9 5 9 5z" />
          <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
        </svg>
        <p className="mt-2">No education data available</p>
        <p className="text-sm">No education documents were found in the uploaded files</p>
      </div>
    );
  }

  const isValid = data.validation_status?.toLowerCase() === 'valid';

  return (
    <div className="space-y-6">
      {/* Student Info */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Student Information</h3>
        <div className="bg-white border rounded-lg divide-y divide-gray-200 px-4">
          <Field label="Student Name" value={data.student_name} />
        </div>
      </div>

      {/* Institution Info */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Institution</h3>
        <div className="bg-white border rounded-lg divide-y divide-gray-200 px-4">
          <Field label="Institution" value={data.institution} />
          <Field label="Country" value={data.country} />
        </div>
      </div>

      {/* Qualification */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Qualification</h3>
        <div className="bg-white border rounded-lg divide-y divide-gray-200 px-4">
          <Field label="Highest Qualification" value={data.highest_qualification} />
          <Field label="Original Grade" value={data.final_grade_original} />
          <Field
            label="French Equivalent (0-20)"
            value={data.french_equivalent_grade_0_20}
            highlight
          />
        </div>
      </div>

      {/* Validation Status */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Validation</h3>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-600">Validation Status:</span>
          <span className={`
            inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
            ${isValid ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}
          `}>
            {data.validation_status || 'Unknown'}
          </span>
        </div>
      </div>

      {/* Remarks */}
      {data.remarks && data.remarks.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Remarks</h3>
          <ul className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
            {data.remarks.map((remark, index) => (
              <li key={index} className="flex items-start space-x-2 text-sm text-blue-800">
                <svg className="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
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
