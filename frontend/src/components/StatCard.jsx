// icon: optional lucide-react component, rendered top-right
export default function StatCard({ label, value, icon: Icon, className = '' }) {
  return (
    <div
      className={`relative min-h-[140px] overflow-hidden rounded-card bg-surface p-5 shadow-card ${className}`}
    >
      {/* left accent bar — the signature stat card motif */}
      <span className="absolute inset-y-0 left-0 w-1 bg-linear-to-b from-primary to-primary-amber" />

      <div className="flex h-full flex-col justify-between pl-3">
        <div className="flex items-start justify-between">
          <span className="text-3xl font-bold tabular-nums text-text-primary">
            {value}
          </span>
          {Icon && <Icon className="h-5 w-5 text-primary" strokeWidth={1.75} />}
        </div>
        <span className="mt-2 text-xs font-medium uppercase tracking-wide text-text-secondary">
          {label}
        </span>
      </div>
    </div>
  );
}
