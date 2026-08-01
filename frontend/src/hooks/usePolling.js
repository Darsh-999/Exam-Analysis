import { useEffect } from 'react';

// Runs `callback` every `intervalMs` while `shouldPoll` is true - stops as
// soon as it flips false (e.g. no documents left in extracting/classifying).
// Plain interval refetching per FRONTEND_DESIGN.md §8 - no websockets/SSE.
export function usePolling(shouldPoll, callback, intervalMs) {
  useEffect(() => {
    if (!shouldPoll) return;
    const interval = setInterval(callback, intervalMs);
    return () => clearInterval(interval);
  }, [shouldPoll, callback, intervalMs]);
}
