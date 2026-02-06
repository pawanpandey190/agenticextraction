import type { FinancialSummary } from '../../services/types';

interface FinancialTabProps {
  data: FinancialSummary | null;
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
      <dd className={`mt-1 text-sm sm:mt-0 sm:col-span-2 ${highlight ? 'font-semibold' : 'text-gray-900'}`}>
        {value ?? <span className="text-gray-400 italic">Not available</span>}
      </dd>
    </div>
  );
}

function formatCurrency(amount: number | null | undefined, currency?: string): string {
  if (amount === null || amount === undefined) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'EUR',
  }).format(amount);
}

export function FinancialTab({ data }: FinancialTabProps) {
  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="mt-2">No financial data available</p>
        <p className="text-sm">No financial documents were found in the uploaded files</p>
      </div>
    );
  }

  const isWorthy = data.worthiness_status?.toLowerCase() === 'worthy';

  return (
    <div className="space-y-6">
      {/* Document Info */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Document Information</h3>
        <div className="bg-white border rounded-lg divide-y divide-gray-200 px-4">
          <Field label="Document Type" value={data.document_type} />
          <Field label="Bank Name" value={data.bank_name} />
          <Field label="Account Holder" value={data.account_holder_name} />
        </div>
      </div>

      {/* Financial Details */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Financial Details</h3>
        <div className="bg-white border rounded-lg divide-y divide-gray-200 px-4">
          <Field label="Base Currency" value={data.base_currency} />
          <Field
            label="Original Amount"
            value={formatCurrency(data.amount_original, data.base_currency || undefined)}
          />
          <Field
            label="Amount (EUR)"
            value={formatCurrency(data.amount_eur, 'EUR')}
            highlight
          />
        </div>
      </div>

      {/* Worthiness Status */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Assessment</h3>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-600">Worthiness Status:</span>
          <span className={`
            inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
            ${isWorthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
          `}>
            {data.worthiness_status || 'Unknown'}
          </span>
        </div>
      </div>

      {/* Remarks */}
      {data.remarks && data.remarks.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Remarks</h3>
          <ul className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 space-y-2">
            {data.remarks.map((remark, index) => (
              <li key={index} className="flex items-start space-x-2 text-sm text-yellow-800">
                <svg className="w-5 h-5 text-yellow-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
