import type { EducationSummary } from '../../services/types';
import { GlassCard } from '../common/GlassComponents';
import { GraduationCap, School, MapPin, Award, Scale, CheckCircle2, AlertCircle, BookOpen, User } from 'lucide-react';

interface EducationTabProps {
  data: EducationSummary | null;
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

export function EducationTab({ data }: EducationTabProps) {
  if (!data) {
    return (
      <GlassCard className="text-center py-16 border-slate-200 shadow-sm bg-white">
        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 border border-slate-100">
          <BookOpen className="w-10 h-10 text-slate-200" />
        </div>
        <h3 className="text-xl font-black text-slate-900 mb-2 uppercase tracking-tight">No Academic Data</h3>
        <p className="text-sm text-slate-400 font-medium max-w-xs mx-auto">No education documents were identified in the uploaded files.</p>
      </GlassCard>
    );
  }

  // No changes needed here, just removing the declaration if it's not used
  // const isValid = data.validation_status?.toLowerCase() === 'valid' || data.validation_status?.toUpperCase() === 'PASS';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Primary Metrics */}
      <div className="space-y-8">
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] flex items-center gap-2">
              <Award className="w-3.5 h-3.5" /> Academic Pillar
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
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">EQUIVALENT FRENCH GRADE</p>
                <h4 className="text-3xl font-black text-slate-900 tracking-tight">{(data.french_equivalent_grade_0_20 ?? 0).toFixed(2)}/20</h4>
              </div>
              <div className={`p-3 rounded-2xl bg-brand-primary/10 text-brand-primary border border-brand-primary/10 shadow-sm`}>
                <Scale className="w-8 h-8" />
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-0 border-slate-200 shadow-sm bg-white overflow-hidden">
            <Field label="Student Holder" value={data.student_name} icon={<User className="w-4 h-4" />} />
            <Field label="Qualification" value={data.highest_qualification} icon={<GraduationCap className="w-4 h-4" />} />
            <Field label="Original Result" value={data.final_grade_original} icon={<Award className="w-4 h-4" />} />
          </GlassCard>
        </div>
      </div>

      {/* Institution Distribution */}
      <div className="space-y-8">
        <div className="space-y-4">
          <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] px-2 flex items-center gap-2">
            <School className="w-3.5 h-3.5" /> Institution Integrity
          </h3>
          <GlassCard className="p-0 border-slate-200 shadow-sm bg-white overflow-hidden">
            <Field label="Educational Body" value={data.institution} icon={<School className="w-4 h-4" />} />
            <Field label="Origin Country" value={data.country} icon={<MapPin className="w-4 h-4" />} />
            <Field
              label="Evaluation Path"
              value={data.validation_status || 'PENDING_VERIFICATION'}
              icon={<CheckCircle2 className="w-4 h-4" />}
              highlight
            />
          </GlassCard>
        </div>

        {data.remarks && (
          <div className="space-y-4">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] px-2 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5" /> Academic Assessment
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
