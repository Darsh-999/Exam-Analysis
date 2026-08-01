import { useRef, useState } from 'react';
import { UploadCloud, X } from 'lucide-react';

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// label: shown above the drop zone. helperText: small text under the icon.
// files: File[] currently selected. onFilesChange: (File[]) => void.
export default function FileDropZone({ label, helperText, accept, files, onFilesChange }) {
  const inputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);

  function addFiles(fileList) {
    onFilesChange([...files, ...Array.from(fileList)]);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragActive(false);
    addFiles(e.dataTransfer.files);
  }

  function removeFile(index) {
    onFilesChange(files.filter((_, i) => i !== index));
  }

  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-text-secondary">{label}</label>

      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          // Space would otherwise scroll the page instead of activating a role="button" element.
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragActive(true);
        }}
        onDragLeave={() => setIsDragActive(false)}
        onDrop={handleDrop}
        className={`flex h-[120px] cursor-pointer flex-col items-center justify-center gap-1 rounded-btn border-2 border-dashed px-4 text-center transition-colors ${
          isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
        }`}
      >
        <UploadCloud className="h-6 w-6 text-text-muted" strokeWidth={1.5} />
        <p className="text-sm text-text-secondary">Drag files here or click to browse</p>
        {helperText && <p className="text-xs text-text-muted">{helperText}</p>}
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          className="hidden"
          onChange={(e) => {
            addFiles(e.target.files);
            e.target.value = ''; // allow re-adding the same file after removing it
          }}
        />
      </div>

      {files.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-2">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1 text-xs text-text-primary"
            >
              <span>{file.name}</span>
              <span className="text-text-muted">({formatFileSize(file.size)})</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(index);
                }}
                aria-label={`Remove ${file.name}`}
                className="text-text-muted hover:text-critical"
              >
                <X className="h-3 w-3" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
