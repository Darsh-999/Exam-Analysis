import { Search } from 'lucide-react';

export default function ProjectsToolbar({ searchValue, onSearchChange }) {
  return (
    <div className="flex items-center rounded-card border border-border bg-surface px-3 py-2 shadow-card">
      <Search className="h-4 w-4 text-text-muted" />
      <input
        type="text"
        value={searchValue}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Search projects..."
        className="ml-2 w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
      />
    </div>
  );
}
