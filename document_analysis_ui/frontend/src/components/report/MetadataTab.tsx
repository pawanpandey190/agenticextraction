import type { ProcessingMetadata } from '../../services/types';
import { GlassCard } from '../common/GlassComponents';
import { Activity, Clock, AlertTriangle, XCircle, CheckCircle2, FileText, Database } from 'lucide-react';

interface MetadataTabProps {
  data: ProcessingMetadata;
}

export function MetadataTab({ data }: MetadataTabProps) {
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="space-y-8">
      {/* Processing Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <GlassCard className="p-6 text-center group hover:border-brand-primary/30 transition-all">
          <FileText className="w-5 h-5 mx-auto mb-3 text-brand-primary opacity-60 group-hover:opacity-100 transition-opacity" />
          <div className="text-2xl font-black text-white mb-1 group-hover:scale-110 transition-transform">
            {data.total_documents_scanned}
          </div>
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Docs Audited</div>
        </GlassCard>

        <GlassCard className="p-6 text-center group hover:border-brand-primary/30 transition-all">
          <Clock className="w-5 h-5 mx-auto mb-3 text-brand-primary opacity-60 group-hover:opacity-100 transition-opacity" />
          <div className="text-2xl font-black text-white mb-1 group-hover:scale-110 transition-transform">
            {formatDuration(data.processing_time_seconds)}
          </div>
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Cycle Time</div>
        </GlassCard>

        <GlassCard className="p-6 text-center group hover:border-brand-primary/30 transition-all">
          <AlertTriangle className="w-5 h-5 mx-auto mb-3 text-amber-400 opacity-60 group-hover:opacity-100 transition-opacity" />
          <div className="text-2xl font-black text-white mb-1 group-hover:scale-110 transition-transform">
            {data.processing_warnings.length}
          </div>
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Warnings</div>
        </GlassCard>

        <GlassCard className="p-6 text-center group hover:border-brand-primary/30 transition-all">
          <XCircle className="w-5 h-5 mx-auto mb-3 text-red-500 opacity-60 group-hover:opacity-100 transition-opacity" />
          <div className="text-2xl font-black text-white mb-1 group-hover:scale-110 transition-transform">
            {data.processing_errors.length}
          </div>
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Failures</div>
        </GlassCard>
      </div>

      {/* Categories Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-4">
          <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2 flex items-center gap-2">
            <Database className="w-4 h-4" /> Corpus Breakdown
          </h3>
          <GlassCard className="p-2 space-y-1">
            {Object.entries(data.documents_by_category).map(([category, count]) => (
              <div key={category} className="flex items-center justify-between py-3 px-4 hover:bg-white/5 rounded-xl transition-colors">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{category}</span>
                <span className="text-sm font-black text-white">{count}</span>
              </div>
            ))}
          </GlassCard>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em] px-2 flex items-center gap-2">
            <Activity className="w-4 h-4" /> Runtime Audit
          </h3>
          <GlassCard className="p-6 min-h-[160px] flex flex-col justify-center">
            {(data.processing_errors.length > 0 || data.processing_warnings.length > 0) ? (
              <div className="space-y-4">
                {data.processing_errors.map((err, i) => (
                  <div key={i} className="flex items-start gap-3 text-red-400">
                    <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <p className="text-xs font-medium leading-relaxed">{err}</p>
                  </div>
                ))}
                {data.processing_warnings.map((warn, i) => (
                  <div key={i} className="flex items-start gap-3 text-amber-400">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <p className="text-xs font-medium leading-relaxed">{warn}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center text-center py-4">
                <div className="p-4 rounded-full bg-brand-secondary/20 text-brand-secondary mb-4">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h4 className="text-white font-bold mb-1">Pristine Execution</h4>
                <p className="text-xs text-slate-500">Processing cycle completed with 100% data integrity.</p>
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
