import { Loader2 } from 'lucide-react';

// size: Tailwind height/width, e.g. 'h-4 w-4' (default) or 'h-8 w-8' for a bigger spinner
export default function Spinner({ className = 'h-4 w-4' }) {
  return <Loader2 className={`animate-spin ${className}`} aria-hidden="true" />;
}
