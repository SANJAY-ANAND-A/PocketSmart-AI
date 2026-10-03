import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, AlertCircle, Check } from 'lucide-react';

interface ImageUploaderProps {
  onImageSelected: (file: File | null) => void;
  maxSizeMB?: number;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onImageSelected,
  maxSizeMB = 5,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setErrorMsg(null);

    // Validate MIME type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setErrorMsg('Unsupported format. Please upload a JPEG, PNG, or WebP image.');
      return;
    }

    // Validate Size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSizeMB) {
      setErrorMsg(`Image exceeds maximum allowed size of ${maxSizeMB} MB (${fileSizeMB.toFixed(1)} MB).`);
      return;
    }

    setSelectedFile(file);
    onImageSelected(file);

    // Create object URL for local preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setErrorMsg(null);
    onImageSelected(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <div className="image-uploader-wrapper">
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />

      {errorMsg && (
        <div className="uploader-error-banner">
          <AlertCircle size={15} />
          <span>{errorMsg}</span>
        </div>
      )}

      {selectedFile && previewUrl ? (
        <div className="uploader-preview-card">
          <div className="preview-image-container">
            <img src={previewUrl} alt="Outfit Preview" className="preview-thumbnail" />
          </div>
          <div className="preview-info">
            <div className="preview-header-row">
              <span className="preview-file-name" title={selectedFile.name}>
                {selectedFile.name}
              </span>
              <button
                type="button"
                className="btn-remove-image"
                onClick={handleRemove}
                title="Remove image"
              >
                <X size={16} />
              </button>
            </div>
            <span className="preview-file-size">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type.split('/')[1].toUpperCase()}
            </span>
            <div className="preview-ready-badge">
              <Check size={13} />
              <span>Ready for Gemini Vision multimodal analysis</span>
            </div>
          </div>
        </div>
      ) : (
        <div
          className={`uploader-dropzone ${dragActive ? 'drag-active' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
        >
          <div className="uploader-icon-ring">
            <UploadCloud size={24} />
          </div>
          <div className="uploader-text-block">
            <p className="uploader-main-text">
              <span className="highlight-text">Click to upload outfit photo</span> or drag and drop
            </p>
            <p className="uploader-hint-text">
              JPEG, PNG, or WebP (max {maxSizeMB} MB). Gemini Vision will inspect colors and patterns to match jewelry.
            </p>
          </div>
          <div className="uploader-badge">
            <ImageIcon size={13} />
            <span>Optional Multimodal Vision Feature</span>
          </div>
        </div>
      )}
    </div>
  );
};
