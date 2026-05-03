import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Loader2 } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'text/html': ['.html', '.htm'],
  'text/markdown': ['.md', '.markdown'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
};

export default function UploadZone() {
  const { uploadFile, isLoading } = useAppStore();
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (accepted: File[]) => {
    if (accepted.length === 0 || uploading) return;
    setUploading(true);
    for (const file of accepted) {
      await uploadFile(file);
    }
    setUploading(false);
  }, [uploadFile, uploading]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    multiple: true,
    disabled: uploading || isLoading,
  });

  return (
    <div className="upload-zone-wrap">
      <div
        {...getRootProps()}
        className={`upload-zone${isDragActive ? ' drag-active' : ''}`}
        id="upload-zone"
      >
        <input {...getInputProps()} />
        {uploading ? (
          <Loader2 size={20} className="upload-zone-icon" style={{ animation: 'spin 1s linear infinite' }} />
        ) : (
          <Upload size={18} className="upload-zone-icon" />
        )}
        <div className="upload-zone-text">
          {uploading ? (
            <span>Uploading…</span>
          ) : isDragActive ? (
            <span><strong>Drop files here</strong></span>
          ) : (
            <span>
              <strong>Upload docs</strong><br />
              PDF, DOCX, MD, HTML, TXT
            </span>
          )}
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
