import React, { useState, useRef, useEffect } from "react";
import { getMriResult, uploadMriScan, type MriResultResponse } from "../services/api";
import "./MriAssessment.css";

interface MriUploadScreenProps {
  assessmentId: string;
  patientName?: string;
  onUploadSuccess: (result: MriResultResponse, previewUrl: string) => void;
  onCancel?: () => void;
}

export const MriUploadScreen: React.FC<MriUploadScreenProps> = ({
  assessmentId,
  patientName,
  onUploadSuccess,
  onCancel,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check if an MRI analysis was already completed for this assessment session
  useEffect(() => {
    let isMounted = true;
    getMriResult(assessmentId)
      .then((existingResult) => {
        if (isMounted && existingResult && existingResult.predicted_class) {
          onUploadSuccess(existingResult, "");
        }
      })
      .catch(() => {
        // A 404 is the expected normal empty state for a new MRI assessment before upload.
        // Never show a 404 as an error on the upload page.
      });

    return () => {
      isMounted = false;
    };
  }, [assessmentId, onUploadSuccess]);

  const handleFile = (file: File) => {
    setErrorMessage(null);
    const validExtensions = [".png", ".jpg", ".jpeg", ".webp", ".bmp"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

    if (!validExtensions.includes(ext) && !file.type.startsWith("image/")) {
      setErrorMessage("Please select a supported image file (PNG, JPEG, WebP, BMP). Note: 3D DICOM (.dcm) files must be exported as 2D slices first.");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setErrorMessage("File exceeds the 15 MB limit. Please select a smaller 2D image file.");
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select an MRI image slice before proceeding.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const result = await uploadMriScan(assessmentId, selectedFile, selectedFile.name);
      onUploadSuccess(result, previewUrl || "");
    } catch (err: any) {
      const msg = err?.message || "Failed to analyze MRI scan. Please verify the file and try again.";
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mri-screen-container">
      <header className="mri-header">
        <span className="mri-badge">Pathway A &bull; Model 4</span>
        <h1 className="mri-title">Brain MRI Scan Analysis</h1>
        <p className="mri-subtitle">
          Upload an individual 2D brain MRI slice for AI-based classification powered by EfficientNetB0.
        </p>
      </header>

      {patientName && (
        <div className="mri-patient-bar">
          <div>
            Patient: <span className="mri-patient-name">{patientName}</span>
          </div>
          <div>ID: {assessmentId.slice(0, 8)}...</div>
        </div>
      )}

      {errorMessage && (
        <div className="mri-error-banner" role="alert">
          {errorMessage}
        </div>
      )}

      <div className="mri-upload-card">
        {!previewUrl ? (
          <div
            className={`mri-dropzone ${isDragging ? "active" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click();
            }}
          >
            <svg
              className="mri-dropzone-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="mri-dropzone-text">Click or drag a 2D brain MRI slice here</p>
            <p className="mri-dropzone-subtext">Individual axial, coronal, or sagittal image slice</p>
            <span className="mri-dropzone-formats">Supports PNG, JPEG, WebP, BMP up to 15 MB</span>
          </div>
        ) : (
          <div className="mri-preview-container">
            <img src={previewUrl} alt="MRI Slice Preview" className="mri-preview-image" />
            <div className="mri-file-meta">
              <strong>{selectedFile?.name}</strong> &bull;{" "}
              {selectedFile ? (selectedFile.size / 1024).toFixed(1) : 0} KB
            </div>
            <button type="button" className="mri-remove-btn" onClick={handleRemove}>
              Select different image
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/bmp"
          className="mri-file-input"
          onChange={handleFileChange}
        />

        <div className="mri-actions">
          {onCancel && (
            <button
              type="button"
              className="mri-btn mri-btn-secondary"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
          <button
            type="button"
            className="mri-btn mri-btn-primary"
            onClick={handleSubmit}
            disabled={!selectedFile || isSubmitting}
          >
            {isSubmitting ? "Analyzing Slice..." : "Analyze MRI Slice"}
          </button>
        </div>
      </div>

      <div className="mri-disclaimer-card">
        <span className="mri-disclaimer-icon">&#9888;</span>
        <p className="mri-disclaimer-text">
          <strong>Academic & Research Prototype Only:</strong> This deep learning model processes individual 2D MRI
          slices and is not a certified diagnostic device. Classification probabilities are statistical estimates
          derived from research dataset labels and must not be used for clinical decision-making or diagnosis.
        </p>
      </div>
    </div>
  );
};
