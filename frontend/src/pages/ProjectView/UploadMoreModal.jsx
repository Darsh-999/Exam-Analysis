import { useState } from 'react';
import Modal from '../../components/Modal';
import Button from '../../components/Button';
import FileDropZone from '../../components/FileDropZone';
import { uploadDocuments } from '../../services/documentsService';
import { ApiError } from '../../services/apiClient';

const ACCEPTED_TYPES = '.pdf,.txt,.json';

// Same two-drop-zone upload flow as the "New Project" modal, minus the
// name/description fields — this just adds more files to an existing project.
export default function UploadMoreModal({ isOpen, onClose, projectId, onUploaded }) {
  const [questionPapers, setQuestionPapers] = useState([]);
  const [syllabi, setSyllabi] = useState([]);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasFiles = questionPapers.length > 0 || syllabi.length > 0;

  function resetAndClose() {
    setQuestionPapers([]);
    setSyllabi([]);
    setError('');
    setIsSubmitting(false);
    onClose();
  }

  async function handleUpload() {
    if (!hasFiles) return;

    setError('');
    setIsSubmitting(true);
    try {
      await uploadDocuments(projectId, { questionPapers, syllabi });
      resetAndClose();
      onUploaded();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
      setIsSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={resetAndClose} title="Upload More Documents">
      <div className="space-y-4">
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
            <Button onClick={handleUpload} disabled={!hasFiles || isSubmitting}>
              {isSubmitting ? 'Uploading…' : 'Upload'}
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
