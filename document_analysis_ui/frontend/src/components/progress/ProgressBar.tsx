interface ProgressBarProps {
  percentage: number;
  showLabel?: boolean;
}

export function ProgressBar({ percentage, showLabel = true }: ProgressBarProps) {
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        {showLabel && (
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Progress</span>
        )}
        <span className="text-sm font-bold text-brand-primary">{Math.round(percentage)}%</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
        <div
          className="bg-brand-primary h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
