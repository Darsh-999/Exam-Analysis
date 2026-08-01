import { AlertCircle } from 'lucide-react';
import Button from './Button';

// The shared "couldn't load this" block. `onRetry` is optional - most
// screens can pass useApiData's `reload` so the user isn't stuck refreshing
// the whole page for a transient network error.
export default function ErrorState({ message, onRetry, className = '' }) {
  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center gap-3 py-16 text-center ${className}`}
    >
      <AlertCircle className="h-8 w-8 text-critical" strokeWidth={1.5} />
      <p className="text-sm text-critical">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
