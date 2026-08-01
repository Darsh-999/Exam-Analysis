import { ChevronDown, ChevronUp } from 'lucide-react';

// topic: { topic, subtopics, weightage, hours } - one entry from a syllabus's content list
export default function TopicCard({ topic, isOpen, onToggle }) {
  return (
    <div className="rounded-card bg-surface shadow-card">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 p-4 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-base font-bold text-text-primary">{topic.topic}</span>
          {/* The extraction pipeline uses -1 as a "not specified in this
              document" sentinel - show nothing rather than a misleading "-1%". */}
          {topic.weightage >= 0 && (
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {topic.weightage}%
            </span>
          )}
          <span className="rounded-full bg-background px-2 py-0.5 text-xs font-medium text-text-secondary">
            {topic.hours} hrs
          </span>
        </div>

        <div className="flex items-center gap-3 text-sm text-text-muted">
          <span>
            {topic.subtopics.length} subtopic{topic.subtopics.length === 1 ? '' : 's'}
          </span>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {isOpen && (
        <ul className="list-disc space-y-1.5 border-t border-border px-4 py-3 pl-10 text-sm text-text-secondary">
          {topic.subtopics.map((subtopic, index) => (
            <li key={`${topic.topic}-${index}`}>{subtopic}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
