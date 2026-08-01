import Spinner from './Spinner';

// The shared "still fetching" block used by every screen instead of each
// one writing its own loading text. `role="status"` + the visually-hidden
// span let screen readers announce it without us needing a separate toast.
export default function LoadingState({ message = 'Loading…', className = '' }) {
  return (
    <div
      role="status"
      className={`flex items-center justify-center gap-2 py-16 text-sm text-text-muted ${className}`}
    >
      <Spinner />
      <span>{message}</span>
    </div>
  );
}
