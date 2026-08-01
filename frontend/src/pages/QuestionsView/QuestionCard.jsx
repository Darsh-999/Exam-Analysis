import { useState } from 'react';
import Modal from '../../components/Modal';

function formatMarks(mark) {
  const value = Number.isInteger(mark) ? mark : mark.toFixed(1);
  return `${value} mark${mark === 1 ? '' : 's'}`;
}

// question: a QuestionOut from the backend, plus a computed `allocationStatus`
// ('allocated' | 'unallocated' | 'multi_allocated') added by QuestionsView.
export default function QuestionCard({ question }) {
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const [isTextExpanded, setIsTextExpanded] = useState(false);

  const imageSrc = `data:image/png;base64,${question.cropped_image}`;
  const metaParts = [question.subject_name, question.subject_code, question.exam_date].filter(
    Boolean
  );

  return (
    <div className="flex flex-col overflow-hidden rounded-card bg-surface shadow-card">
      <div className="relative bg-background">
        <img
          src={imageSrc}
          alt={`Question ${question.question_number}`}
          onClick={() => setIsLightboxOpen(true)}
          className="h-40 w-full cursor-zoom-in object-contain"
        />
        <div className="absolute right-2 top-2 flex gap-1.5">
          <span className="rounded-full bg-nav/80 px-2 py-0.5 text-xs font-medium text-white">
            Q{question.question_number}
          </span>
          <span className="rounded-full bg-primary/90 px-2 py-0.5 text-xs font-medium text-white">
            {formatMarks(question.mark)}
          </span>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <p
          onClick={() => setIsTextExpanded((expanded) => !expanded)}
          title={question.question}
          className={`cursor-pointer text-sm text-text-primary ${
            isTextExpanded ? '' : 'line-clamp-3'
          }`}
        >
          {question.question}
        </p>

        {metaParts.length > 0 && (
          <p className="text-xs text-text-muted">{metaParts.join(' · ')}</p>
        )}

        <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-2">
          {question.topic.length === 0 ? (
            <span className="rounded-full bg-background px-2 py-0.5 text-xs text-text-muted">
              Unallocated
            </span>
          ) : (
            question.topic.map((t) => (
              <span
                key={t.topic}
                title={t.subtopics.join(', ')}
                className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
              >
                {t.topic}
              </span>
            ))
          )}
          {question.topic.length >= 2 && (
            <span
              title="Mapped to multiple topics"
              className="rounded-full bg-warning/10 px-1.5 py-0.5 text-xs font-semibold text-warning"
            >
              ×{question.topic.length}
            </span>
          )}
        </div>
      </div>

      <Modal
        isOpen={isLightboxOpen}
        onClose={() => setIsLightboxOpen(false)}
        title={`Q${question.question_number}`}
      >
        <img src={imageSrc} alt={`Question ${question.question_number}`} className="w-full" />
      </Modal>
    </div>
  );
}
