// Only rendered when there's more than one syllabus - a single document
// shows its content directly, no tabs needed.
export default function SyllabusSelector({ syllabi, selectedId, onSelect }) {
  if (syllabi.length <= 1) return null;

  return (
    <div className="flex flex-wrap gap-2 border-b border-border">
      {syllabi.map((syllabus) => (
        <button
          key={syllabus.id}
          type="button"
          onClick={() => onSelect(syllabus.id)}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            syllabus.id === selectedId
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          {syllabus.filename}
        </button>
      ))}
    </div>
  );
}
