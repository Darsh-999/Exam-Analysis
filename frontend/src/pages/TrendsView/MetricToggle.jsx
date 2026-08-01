// Small two-option switch: "most asked" (count) vs "most heavily weighted" (marks).
export default function MetricToggle({ value, onChange }) {
  return (
    <div className="flex overflow-hidden rounded-btn border border-border text-xs font-medium">
      {['count', 'marks'].map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={`px-3 py-1.5 capitalize transition-colors ${
            value === option
              ? 'bg-primary text-white'
              : 'bg-surface text-text-secondary hover:bg-background'
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  );
}
