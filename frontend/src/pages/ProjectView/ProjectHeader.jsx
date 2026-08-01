import { Upload } from 'lucide-react';
import Button from '../../components/Button';

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function ProjectHeader({ summary, onUploadMoreClick }) {
  return (
    <div className="flex items-start justify-between">
      <div>
        <h1 className="text-[28px] font-bold text-text-primary">{summary.name}</h1>
        {summary.description && (
          <p className="mt-1 text-sm text-text-secondary">{summary.description}</p>
        )}
        <p className="mt-2 text-xs text-text-muted">
          Created by {summary.created_by} on {formatDate(summary.created_at)}
        </p>
      </div>

      <Button variant="secondary" onClick={onUploadMoreClick}>
        <Upload className="h-4 w-4" /> Upload More
      </Button>
    </div>
  );
}
