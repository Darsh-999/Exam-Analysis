import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Modal from '../../components/Modal';
import Button from '../../components/Button';
import FileDropZone from '../../components/FileDropZone';
import { createProject } from '../../services/projectsService';
import { uploadDocuments } from '../../services/documentsService';
import { ApiError } from '../../services/apiClient';

const ACCEPTED_TYPES = '.pdf,.txt,.json';
const inputClasses =
  'w-full rounded-btn border border-border px-3 text-sm text-text-primary focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20';

export default function NewProjectModal({ isOpen, onClose }) {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [questionPapers, setQuestionPapers] = useState([]);
  const [syllabi, setSyllabi] = useState([]);
  const [nameTouched, setNameTouched] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasFiles = questionPapers.length > 0 || syllabi.length > 0;
  const canSubmit = name.trim().length > 0 && hasFiles;

  function resetAndClose() {
    setName('');
    setDescription('');
    setQuestionPapers([]);
    setSyllabi([]);
    setNameTouched(false);
    setError('');
    setIsSubmitting(false);
    onClose();
  }

  async function handleAnalyze() {
    setNameTouched(true);
    if (!canSubmit) return;

    setError('');
    setIsSubmitting(true);
    try {
      // Two write calls: create the project, then upload its files. The
      // upload call returns as soon as the pipeline has been kicked off
      // (HTTP 202) — extraction/classification finish in the background,
      // which is why we navigate away immediately instead of waiting.
      const project = await createProject({
        name: name.trim(),
        description: description.trim() || undefined,
      });
      await uploadDocuments(project.id, { questionPapers, syllabi });

      resetAndClose();
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
      setIsSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={resetAndClose} title="New Project">
      <div className="space-y-4">
        <div>
          <label htmlFor="project-name" className="mb-1.5 block text-xs font-medium text-text-secondary">
            Project Name <span className="text-critical">*</span>
          </label>
          <input
            id="project-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => setNameTouched(true)}
            className={`h-11 ${inputClasses}`}
          />
          {nameTouched && name.trim().length === 0 && (
            <p className="mt-1 text-xs text-critical">Project name is required.</p>
          )}
        </div>

        <div>
          <label
            htmlFor="project-description"
            className="mb-1.5 block text-xs font-medium text-text-secondary"
          >
            Description <span className="text-text-muted">(Optional)</span>
          </label>
          <textarea
            id="project-description"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className={`py-2 ${inputClasses}`}
          />
        </div>

        <FileDropZone
          label="Question Papers"
          helperText="PDF, TXT or JSON — multiple files allowed"
          accept={ACCEPTED_TYPES}
          files={questionPapers}
          onFilesChange={setQuestionPapers}
        />

        <FileDropZone
          label="Syllabus / Topic List"
          helperText="PDF, TXT or JSON — multiple files allowed"
          accept={ACCEPTED_TYPES}
          files={syllabi}
          onFilesChange={setSyllabi}
        />

        {error && <p className="text-xs text-critical">{error}</p>}

        <div className="flex flex-col items-end gap-1.5 pt-2">
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={resetAndClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button onClick={handleAnalyze} disabled={!canSubmit || isSubmitting}>
              {isSubmitting ? 'Analyzing…' : 'Analyze'}
            </Button>
          </div>
          {!hasFiles && (
            <p className="text-xs text-text-muted">Add at least one file to continue</p>
          )}
        </div>
      </div>
    </Modal>
  );
}
