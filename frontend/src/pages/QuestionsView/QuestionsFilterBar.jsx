import { Search } from 'lucide-react';

const ALLOCATION_OPTIONS = [
  { value: '', label: 'All' },
  { value: 'allocated', label: 'Allocated' },
  { value: 'unallocated', label: 'Unallocated' },
  { value: 'multi_allocated', label: 'Multi-allocated' },
];

const selectClasses =
  'h-10 rounded-btn border border-border bg-surface px-3 text-sm text-text-primary focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20';

export default function QuestionsFilterBar({
  subjects,
  topics,
  subjectValue,
  onSubjectChange,
  topicValue,
  onTopicChange,
  allocationValue,
  onAllocationChange,
  keywordValue,
  onKeywordChange,
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={subjectValue}
        onChange={(e) => onSubjectChange(e.target.value)}
        className={selectClasses}
      >
        <option value="">All Subjects</option>
        {subjects.map((subject) => (
          <option key={subject.value} value={subject.value}>
            {subject.label}
          </option>
        ))}
      </select>

      <input
        list="topic-options"
        value={topicValue}
        onChange={(e) => onTopicChange(e.target.value)}
        placeholder="All Topics"
        className={`w-48 ${selectClasses}`}
      />
      <datalist id="topic-options">
        {topics.map((topic) => (
          <option key={topic} value={topic} />
        ))}
      </datalist>

      <div className="flex overflow-hidden rounded-btn border border-border">
        {ALLOCATION_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onAllocationChange(option.value)}
            className={`h-10 px-3 text-sm font-medium transition-colors ${
              allocationValue === option.value
                ? 'bg-primary text-white'
                : 'bg-surface text-text-secondary hover:bg-background'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="flex h-10 min-w-[220px] flex-1 items-center rounded-btn border border-border bg-surface px-3">
        <Search className="h-4 w-4 text-text-muted" />
        <input
          type="text"
          value={keywordValue}
          onChange={(e) => onKeywordChange(e.target.value)}
          placeholder="Search question text..."
          className="ml-2 w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
        />
      </div>
    </div>
  );
}
