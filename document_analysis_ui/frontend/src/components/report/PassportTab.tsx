import type { PassportDetails } from '../../services/types';
import { GlassCard } from '../common/GlassComponents';
import { User, Shield, Globe, Calendar, Info, AlertCircle } from 'lucide-react';

interface PassportTabProps {
  data: PassportDetails | null;
}

interface FieldProps {
  label: string;
  value: string | number | null | undefined;
  icon: React.ReactNode;
}

function Field({ label, value, icon }: FieldProps) {
  return (
    <div className="flex items-center justify-between py-4 group hover:bg-slate-50 transition-colors px-4 rounded-xl border-b border-slate-50 last:border-0">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-slate-100 text-slate-400 group-hover:text-brand-primary transition-colors">
          {icon}
        </div>
        <dt className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">{label}</dt>
      </div>
      <dd className="text-sm font-black text-slate-900">
        {value ?? <span className="text-slate-300 italic font-medium">Not available</span>}
      </dd>
    </div>
  );
}

export function PassportTab({ data }: PassportTabProps) {
  if (!data) {
    return (
      <GlassCard className="text-center py-16 border-slate-200 shadow-sm bg-white">
        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 border border-slate-100">
          <Shield className="w-10 h-10 text-slate-200" />
        </div>
        <h3 className="text-xl font-black text-slate-900 mb-2 uppercase tracking-tight">No Identity Data</h3>
        <p className="text-sm text-slate-400 font-medium max-w-xs mx-auto">No passport documents were identified in the uploaded files.</p>
      </GlassCard>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Primary Info */}
      <div className="space-y-8">
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] flex items-center gap-2">
              <User className="w-3.5 h-3.5" /> Identity Pillar
            </h3>
            {data.french_equivalence && (
              <div className="px-3 py-1 rounded-full bg-brand-primary/10 border border-brand-primary/20 text-[10px] font-black uppercase tracking-widest text-brand-primary">
                {data.french_equivalence}
              </div>
            )}
          </div>
          <GlassCard className="p-2 space-y-1">
            <Field label="First Name" value={data.first_name} icon={<User className="w-4 h-4" />} />
            <Field label="Last Name" value={data.last_name} icon={<User className="w-4 h-4" />} />
            <Field label="Date of Birth" value={data.date_of_birth} icon={<Calendar className="w-4 h-4" />} />
          </GlassCard>
        </div>

        <div className="space-y-4">
          <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] px-2 flex items-center gap-2">
            <Shield className="w-3.5 h-3.5" /> Validation Integrity
          </h3>
          <GlassCard className="p-0 border-slate-200 shadow-sm bg-white overflow-hidden">
            <Field label="Passport ID" value={data.passport_number} icon={<Info className="w-4 h-4" />} />
            <Field label="Issuing State" value={data.issuing_country} icon={<Globe className="w-4 h-4" />} />
            <Field label="Issue Date" value={data.issue_date} icon={<Calendar className="w-4 h-4" />} />
            <Field label="Expiry Date" value={data.expiry_date} icon={<Calendar className="w-4 h-4" />} />
          </GlassCard>
        </div>
      </div>

      {/* Technical Info & Remarks */}
      <div className="space-y-8">
        <div className="space-y-4">
          <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] px-2 flex items-center gap-2">
            <Info className="w-3.5 h-3.5" /> Machine Readable Zone (MRZ)
          </h3>
          <GlassCard className="p-6 font-mono text-xs leading-loose tracking-wider break-all bg-slate-900 text-brand-primary shadow-xl border-slate-900 rounded-2xl">
            <div className="opacity-90 mb-2 whitespace-pre-wrap">{data.mrz_line1 || 'LINE_1_STUB_DATA'}</div>
            <div className="opacity-90 whitespace-pre-wrap">{data.mrz_line2 || 'LINE_2_STUB_DATA'}</div>
          </GlassCard>
        </div>

        {data.remarks && (
          <div className="space-y-4">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] px-2 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5" /> Auditor Insights
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
