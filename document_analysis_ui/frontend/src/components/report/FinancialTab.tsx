import type { FinancialSummary } from '../../services/types';
import { GlassCard } from '../common/GlassComponents';
import { CreditCard, Landmark, User, DollarSign, Wallet, AlertCircle, CheckCircle2, TrendingUp, Shield } from 'lucide-react';

interface FinancialTabProps {
  data: FinancialSummary | null;
}

interface FieldProps {
  label: string;
  value: string | number | null | undefined;
  icon: React.ReactNode;
  highlight?: boolean;
}

function Field({ label, value, icon, highlight = false }: FieldProps) {
  return (
    <div className={`flex items-center justify-between py-4 group hover:bg-slate-50 transition-colors px-4 rounded-xl border-b border-slate-50 last:border-0 ${highlight ? 'bg-brand-primary/5 border border-brand-primary/10' : ''}`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${highlight ? 'bg-brand-primary/10 text-brand-primary' : 'bg-slate-100 text-slate-400'} group-hover:text-brand-primary transition-colors`}>
          {icon}
        </div>
        <dt className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">{label}</dt>
      </div>
      <dd className={`text-sm font-black ${highlight ? 'text-brand-primary text-lg' : 'text-slate-900'}`}>
        {value ?? <span className="text-slate-300 italic font-medium">Not available</span>}
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
      <GlassCard className="text-center py-16 border-slate-200 shadow-sm bg-white">
        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 border border-slate-100">
          <Wallet className="w-10 h-10 text-slate-200" />
        </div>
        <h3 className="text-xl font-black text-slate-900 mb-2 uppercase tracking-tight">No Financial Data</h3>
        <p className="text-sm text-slate-400 font-medium max-w-xs mx-auto">No financial documents were identified in the uploaded files.</p>
      </GlassCard>
    );
  }

  const isWorthy = data.worthiness_status?.toUpperCase() === 'PASS';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Primary Metrics */}
      <div className="space-y-8">
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] flex items-center gap-2">
              <TrendingUp className="w-3.5 h-3.5" /> Liquidity Matrix
            </h3>
            {data.french_equivalence && (
              <div className="px-3 py-1 rounded-full bg-brand-primary/10 border border-brand-primary/20 text-[10px] font-black uppercase tracking-widest text-brand-primary">
                {data.french_equivalence}
              </div>
            )}
          </div>
          <GlassCard className="p-6 bg-white border-slate-200 shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">AGGREGATE VALUATION (EUR)</p>
                <h4 className="text-3xl font-black text-slate-900 tracking-tight">{formatCurrency(data.amount_eur, 'EUR')}</h4>
              </div>
              <div className={`p-3 rounded-2xl ${isWorthy ? 'bg-brand-secondary/10 text-brand-secondary' : 'bg-red-50 text-red-500'} border border-current/10 shadow-sm`}>
                {isWorthy ? <CheckCircle2 className="w-8 h-8" /> : <AlertCircle className="w-8 h-8" />}
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-0 border-slate-200 shadow-sm bg-white overflow-hidden">
            <Field label="Document Type" value={data.document_type} icon={<CreditCard className="w-4 h-4" />} />
            <Field label="Bank Institution" value={data.bank_name} icon={<Landmark className="w-4 h-4" />} />
            <Field label="Account Holder" value={data.account_holder_name} icon={<User className="w-4 h-4" />} />
          </GlassCard>
        </div>
      </div>

      {/* Financial Distribution */}
      <div className="space-y-8">
        <div className="space-y-4">
          <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] px-2 flex items-center gap-2">
            <DollarSign className="w-3.5 h-3.5" /> Currency Intelligence
          </h3>
          <GlassCard className="p-0 border-slate-200 shadow-sm bg-white overflow-hidden">
            <Field label="Reported Base" value={data.base_currency} icon={<DollarSign className="w-4 h-4" />} />
            <Field
              label="Original Float"
              value={formatCurrency(data.amount_original, data.base_currency || undefined)}
              icon={<Wallet className="w-4 h-4" />}
            />
            <Field
              label="French Threshold"
              value={data.french_equivalence || 'Non Évalué'}
              icon={<Shield className="w-4 h-4" />}
              highlight
            />
          </GlassCard>
        </div>

        {data.remarks && (
          <div className="space-y-4">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] px-2 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5" /> Financial Assessment
            </h3>
            <GlassCard className="p-6 bg-slate-50 border-slate-200 shadow-sm">
              <p className="text-sm text-slate-600 leading-relaxed italic font-medium">
                "{data.remarks}"
              </p>
            </GlassCard>
          </div>
        )}
      </div>
    </div>
  );
}
