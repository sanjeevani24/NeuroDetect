import React from "react";
import type { MriResultResponse } from "../services/api";
import "./MriAssessment.css";

interface MriResultsScreenProps {
  result: MriResultResponse;
  previewUrl?: string | null;
  onStartNewAssessment: () => void;
}

export const MriResultsScreen: React.FC<MriResultsScreenProps> = ({
  result,
  previewUrl,
  onStartNewAssessment,
}) => {
  const {
    predicted_class,
    class_probabilities,
    binary_prediction,
    binary_probabilities,
    model_name,
    model_version,
    image_filename,
    disclaimer,
  } = result;

  const getPredColorClass = (cls: string) => {
    switch (cls) {
      case "Non-Demented":
        return "mri-pred-non-demented";
      case "Very Mildly Demented":
      case "Mildly Demented":
        return "mri-pred-mild";
      case "Moderately Demented":
        return "mri-pred-moderate";
      default:
        return "";
    }
  };

  const isDementia = binary_prediction === "Dementia";
  const binaryConfidence = isDementia
    ? (binary_probabilities.dementia * 100).toFixed(1)
    : (binary_probabilities.no_dementia * 100).toFixed(1);

  const classesOrdered = [
    "Non-Demented",
    "Very Mildly Demented",
    "Mildly Demented",
    "Moderately Demented",
  ];

  return (
    <div className="mri-screen-container">
      <header className="mri-header">
        <span className="mri-badge">Pathway A &bull; Model 4 Analysis</span>
        <h1 className="mri-title">MRI Classification Result</h1>
        <p className="mri-subtitle">
          Automated 2D slice feature extraction and classification using deep convolutional neural network.
        </p>
      </header>

      {/* Primary Result Summary */}
      <div className="mri-results-summary-card">
        {previewUrl && (
          <div className="mri-result-slice-wrapper">
            <img src={previewUrl} alt="Analyzed MRI slice" className="mri-result-slice-img" />
            <span className="mri-result-slice-label">{image_filename || "MRI Slice"}</span>
          </div>
        )}

        <div className="mri-primary-prediction-box">
          <span className="mri-pred-label-heading">Predicted Category</span>
          <h2 className={`mri-pred-class-title ${getPredColorClass(predicted_class)}`}>
            {predicted_class}
          </h2>

          <div className="mri-binary-badge-container">
            <span className={`mri-binary-tag ${isDementia ? "dementia" : "no-dementia"}`}>
              {binary_prediction}
            </span>
            <span className="mri-binary-subtext">
              ({binaryConfidence}% binary grouping confidence)
            </span>
          </div>

          <p style={{ margin: "0.75rem 0 0", fontSize: "0.85rem", color: "#64748b", lineHeight: 1.4 }}>
            Classified by {model_name} ({model_version}) from a single 2D cross-sectional slice.
          </p>
        </div>
      </div>

      {/* 4-Class Probability Breakdown */}
      <div className="mri-breakdown-card">
        <h3 className="mri-section-title">4-Class Probability Breakdown</h3>
        <div className="mri-prob-bars">
          {classesOrdered.map((clsName) => {
            const prob = class_probabilities[clsName] ?? 0;
            const pct = (prob * 100).toFixed(1);
            const isHighest = clsName === predicted_class;

            return (
              <div key={clsName} className="mri-prob-row">
                <div className="mri-prob-header">
                  <span>{clsName}</span>
                  <span className="mri-prob-percentage">{pct}%</span>
                </div>
                <div className="mri-bar-track">
                  <div
                    className={`mri-bar-fill ${isHighest ? "highlight" : "normal"}`}
                    style={{ width: `${Math.max(Number(pct), 2)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Disclaimer Card */}
      <div className="mri-disclaimer-card">
        <span className="mri-disclaimer-icon">&#9888;</span>
        <p className="mri-disclaimer-text">
          <strong>Research Use Only:</strong> {disclaimer}
        </p>
      </div>

      {/* Action Buttons */}
      <div className="mri-actions" style={{ justifyContent: "center", marginTop: "2rem" }}>
        <button
          type="button"
          className="mri-btn mri-btn-secondary"
          onClick={() => window.print()}
        >
          Print / Export Report
        </button>
        <button
          type="button"
          className="mri-btn mri-btn-primary"
          onClick={onStartNewAssessment}
        >
          Start New Assessment
        </button>
      </div>
    </div>
  );
};
