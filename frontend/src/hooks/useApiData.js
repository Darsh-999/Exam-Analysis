import { useCallback, useEffect, useRef, useState } from 'react';

// Every screen fetches something on mount and needs the same
// loading/error/data bookkeeping — this hook does that once so screens don't
// each repeat it.
//
// `fetcher` must be wrapped in useCallback by the caller (so its identity
// only changes when the values it depends on, e.g. projectId, change) -
// otherwise this would refetch on every render.
export function useApiData(fetcher) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);
  const previousFetcherRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    const isNewResource = previousFetcherRef.current !== fetcher;
    previousFetcherRef.current = fetcher;

    // Only show the blocking loading state for a genuinely new resource
    // (first mount, or the fetcher's own inputs changed, e.g. a different
    // projectId). A reload() of the SAME resource - like the Individual
    // Project screen's polling while documents process - keeps showing the
    // last good data while it refreshes in the background, instead of
    // blanking the whole screen every few seconds.
    if (isNewResource) {
      setIsLoading(true);
      setData(null);
    }
    setError(null);

    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [fetcher, reloadToken]);

  const reload = useCallback(() => setReloadToken((token) => token + 1), []);

  return { data, error, isLoading, reload };
}
