import type { CrossValidation } from '../../services/types';
import { GlassCard } from '../common/GlassComponents';
import { ShieldCheck, XCircle, AlertCircle, User, Calendar, Info, CheckCircle2 } from 'lucide-react';

interface CrossValidationTabProps {
  data: CrossValidation | null;
}

interface MatchIndicatorProps {
  label: string;
  isMatch: boolean | null;
  score?: number | null;
  icon: React.ReactNode;
}

function MatchIndicator({ label, isMatch, score, icon }: MatchIndicatorProps) {
  if (isMatch === null) {
    return (
      <div className="flex items-center justify-between py-4 px-4 rounded-xl hover:bg-white/5 transition-colors">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-white/5 text-slate-500">
            {icon}
          </div>
          <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{label}</span>
        </div>
        <span className="text-xs font-bold text-slate-600 uppercase">Not available</span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between py-4 px-4 rounded-xl hover:bg-white/5 transition-colors group">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-white/5 ${isMatch ? 'text-brand-secondary' : 'text-red-400'} group-hover:scale-110 transition-transform`}>
          {icon}
        </div>
        <span className="text-xs font-bold text-slate-400 uppercase tracking-widest group-hover:text-white transition-colors">{label}</span>
      </div>
      <div className="flex items-center space-x-4">
        {score !== null && score !== undefined && (
          <span className="text-[10px] font-black text-brand-primary uppercase tracking-widest opacity-60">
            {(score * 100).toFixed(1)}% CONFIDENCE
          </span>
        )}
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-[10px] font-black uppercase tracking-widest ${isMatch ? 'text-brand-secondary border-brand-secondary/20 bg-brand-secondary/10' : 'text-red-400 border-red-400/20 bg-red-400/10'}`}>
          {isMatch ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
          {isMatch ? 'MATCH' : 'MISMATCH'}
        </div>
      </div>
    </div>
  );
}

export function CrossValidationTab({ data }: CrossValidationTabProps) {
  if (!data) {
    return (
      <GlassCard className="text-center py-16">
        <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShieldCheck className="w-10 h-10 text-slate-600" />
        </div>
        <h3 className="text-xl font-bold text-white mb-2">No Validation Data</h3>
        <p className="text-slate-400 max-w-xs mx-auto">Cross-validation requires multiple document types to be present.</p>
      </GlassCard>
    );
  }

  const allMatch = data.name_match === true && data.dob_match === true;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Overview Card */}
      <div className="space-y-8">
        <div className="space-y-4">
          <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" /> Integrity Status
          </h3>
          <GlassCard className={`p-6 border-2 transition-all ${allMatch ? 'border-brand-secondary/30 bg-brand-secondary/5' : 'border-amber-400/30 bg-amber-400/5'}`}>
            <div className="flex items-center gap-4 mb-4">
              <div className={`p-4 rounded-[2rem] ${allMatch ? 'bg-brand-secondary/20 text-brand-secondary' : 'bg-amber-400/20 text-amber-400'}`}>
                {allMatch ? <CheckCircle2 className="w-10 h-10" /> : <AlertCircle className="w-10 h-10" />}
              </div>
              <div>
                <h4 className="text-xl font-black text-white">{allMatch ? 'Data Consistent' : 'Verification Warning'}</h4>
                <p className="text-xs text-slate-400 font-medium uppercase tracking-widest mt-1">Cross-Document Audit Complete</p>
              </div>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed italic border-t border-white/5 pt-4">
              {allMatch
                ? "All personally identifiable information (PII) is perfectly synchronized across the submitted identity, academic, and financial dossiers."
                : "Discrepancies detected in PII fields across documents. Manual auditor review is highly recommended for this application."}
            </p>
          </GlassCard>
        </div>
      </div>

      {/* Detailed Validation */}
      <div className="space-y-8">
        <div className="space-y-4">
          <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2 flex items-center gap-2">
            <Info className="w-4 h-4" /> Point-by-Point Audit
          </h3>
          <GlassCard className="p-2 space-y-1">
            <MatchIndicator
              label="FullName Consistency"
              isMatch={data.name_match}
              score={data.name_match_score}
              icon={<User className="w-4 h-4" />}
            />
            <MatchIndicator
              label="Birthdate Alignment"
              isMatch={data.dob_match}
              icon={<Calendar className="w-4 h-4" />}
            />
          </GlassCard>
        </div>

        {data.remarks && (
          <div className="space-y-4">
            <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" /> Cross-Agent Remarks
            </h3>
            <GlassCard className="p-6 bg-brand-primary/5 border-brand-primary/20">
              <p className="text-sm text-slate-300 leading-relaxed">
                {data.remarks}
              </p>
            </GlassCard>
          </div>
        )}
      </div>
    </div>
  );
}
