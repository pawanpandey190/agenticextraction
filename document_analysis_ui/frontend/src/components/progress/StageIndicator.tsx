import { STAGE_NAMES } from '../../hooks/useProgress';

interface StageIndicatorProps {
  currentStageIndex: number;
  isComplete: boolean;
}

const STAGE_LABELS: Record<string, string> = {
  'DocumentScanner': 'Scanning Documents',
  'DocumentClassifier': 'Classifying Documents',
  'AgentDispatcher': 'Processing with AI',
  'ResultNormalizer': 'Normalizing Results',
  'CrossValidator': 'Cross-validating Data',
  'OutputGenerator': 'Generating Output',
};

export function StageIndicator({ currentStageIndex, isComplete }: StageIndicatorProps) {
  return (
    <div className="space-y-3">
      {STAGE_NAMES.map((stage, index) => {
        const isActive = index === currentStageIndex && !isComplete;
        const isDone = index < currentStageIndex || isComplete;
        const isPending = index > currentStageIndex && !isComplete;

        return (
          <div key={stage} className="flex items-center space-x-3">
            {/* Status icon */}
            <div className={`
              flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
              ${isDone ? 'bg-green-100' : isActive ? 'bg-blue-100' : 'bg-gray-100'}
            `}>
              {isDone ? (
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : isActive ? (
                <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <span className="w-2 h-2 bg-gray-400 rounded-full" />
              )}
            </div>

            {/* Label */}
            <span className={`
              text-sm font-medium
              ${isDone ? 'text-green-700' : isActive ? 'text-blue-700' : 'text-gray-400'}
            `}>
              {STAGE_LABELS[stage] || stage}
            </span>
          </div>
        );
      })}
    </div>
  );
}
