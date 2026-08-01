import Button from './Button';

// icon: optional lucide-react component
// actionLabel + onAction: optional primary action button
export default function EmptyState({ icon: Icon, message, actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      {Icon && <Icon className="h-10 w-10 text-text-muted" strokeWidth={1.5} />}
      <p className="text-sm text-text-muted">{message}</p>
      {actionLabel && onAction && <Button onClick={onAction}>{actionLabel}</Button>}
    </div>
  );
}
