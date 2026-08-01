import { useState } from 'react';
import TopicCard from './TopicCard';

// All topics collapsed except the first, per FRONTEND_DESIGN.md §5. Mount
// this with `key={selectedSyllabusId}` from the parent so switching
// syllabus documents resets back to that default instead of keeping stale
// open/closed state around.
export default function TopicAccordion({ topics }) {
  const [openIndices, setOpenIndices] = useState(() => new Set(topics.length > 0 ? [0] : []));

  function toggle(index) {
    setOpenIndices((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }

  return (
    <div className="space-y-3">
      {topics.map((topic, index) => (
        <TopicCard
          key={topic.topic}
          topic={topic}
          isOpen={openIndices.has(index)}
          onToggle={() => toggle(index)}
        />
      ))}
    </div>
  );
}
