import { Hourglass, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

// One entry per status the backend can report for a document/paper.
const STATUS_CONFIG = {
  extracting: {
    label: 'Extracting',
    icon: Hourglass,
    classes: 'bg-warning/10 text-warning',
  },
  classifying: {
    label: 'Classifying',
    icon: Loader2,
    classes: 'bg-warning/10 text-warning',
    spin: true,
  },
  completed: {
    label: 'Completed',
    icon: CheckCircle2,
    classes: 'bg-success/10 text-success',
  },
  failed: {
    label: 'Failed',
    icon: AlertCircle,
    classes: 'bg-critical/10 text-critical',
  },
};

// errorMessage: shown as a native tooltip on hover, only used for 'failed'
export default function StatusBadge({ status, errorMessage }) {
  const config = STATUS_CONFIG[status];
  if (!config) return null;

  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${config.classes}`}
      title={status === 'failed' ? errorMessage : undefined}
    >
      <Icon className={`h-3.5 w-3.5 ${config.spin ? 'animate-spin' : ''}`} />
      {config.label}
    </span>
  );
}
