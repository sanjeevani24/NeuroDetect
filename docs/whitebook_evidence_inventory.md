# NeuroDetect Semester VII White Book — Evidence Inventory

This document provides a complete audit trail mapping every claim, performance metric, architectural diagram, figure, and code implementation cited in the **NeuroDetect Semester VII White Book** (`docs/NeuroDetect_Semester_VII_WhiteBook.docx`) to its exact source file, test artifact, or codebase location.

---

## 1. Project Identity & Institutional Metadata

| Metadata Field | Value in Report | Verification Source |
|---|---|---|
| Institution | Somaiya Vidyavihar University, K. J. Somaiya School of Engineering | Department of Information Technology Curriculum, B.Tech AIDS 2023-27 |
| Project Title | Early Prediction of Pseudo Dementia and Alzheimer’s Using Deep Learning and Multimodal Patient Data | Semester VI Approved Report (`FINAL_merged.pdf`), Slide Deck (`Group10__...pdf`) |
| Guide | Ms. Bushra Shaikh | Project Allotment Records, Semester VI Report Title Page |
| Group Members | Sanjeevani Chaurasia (16014223073)<br>Soham Redkar (16014223081)<br>Tanish Shetty (16014223088)<br>Aayush More (16014223104) | Roll call and project registration documentation |
| Academic Stage | Semester VII (Capstone Project Phase II) | Current Term: Academic Year 2024-2025 |

---

## 2. Model Performance Metrics Evidence Trail

### Model 1: Cognitive Performance Regressor (XGBoost)
- **Source Artifact:** `backend/models/model1/model1_cognitive_package/training_summary.json`
- **Metadata:** `backend/models/model1/model1_cognitive_package/model_metadata.json`
- **Feature Importance:** `backend/models/model1/model1_cognitive_package/feature_importance_xgboost.csv`
- **Trained Model Binary:** `backend/models/model1/model1_cognitive_package/model1_cognitive_xgboost.json`

| Metric / Parameter | Value in White Book | Exact Value in Repository Source | Status |
|---|---|---|---|
| Model Algorithm | XGBRegressor | `"model_type": "XGBRegressor"` | VERIFIED |
| Feature Count | 47 engineered features | `"feature_count": 47` in `training_summary.json` | VERIFIED |
| Training Dataset Size | 16,000 synthetic participant rows | `"training_rows": 16000` | VERIFIED |
| Validation Size | 2,000 rows | `"validation_rows": 2000` | VERIFIED |
| Test Dataset Size | 2,000 rows | `"test_rows": 2000` | VERIFIED |
| Test $R^2$ Score | 0.9899 (98.99%) | `"R2": 0.9899399403545585` | VERIFIED |
| Test MAE | 1.1363 points (on 0-100 scale) | `"MAE": 1.1362963236236572` | VERIFIED |
| Test RMSE | 1.4322 points | `"RMSE": 1.4322377495302412` | VERIFIED |
| Test Median AE | 0.9512 points | `"MedianAE": 0.9511526489257776` | VERIFIED |
| Data Provenance | Synthetic cognitive game simulations | `"data_type": "synthetic"`, `"clinical_validation": false` | VERIFIED |

### Model 2: Mental Health Psychometric Scoring Engine
- **Source Implementation:** `backend/app/services/mental_health_service.py`
- **Router Implementation:** `backend/app/routers/mental_health.py`
- **Questionnaire Standards:** PHQ-9 (Kroenke et al., 2001) & GAD-7 (Spitzer et al., 2006)

| Parameter / Logic | Value in White Book | Code Location | Status |
|---|---|---|---|
| PHQ-9 Range | 0 to 27 points (9 items, 0-3 scale) | `mental_health_service.py` | VERIFIED |
| GAD-7 Range | 0 to 21 points (7 items, 0-3 scale) | `mental_health_service.py` | VERIFIED |
| Clinical Cutoff ($S \ge 10$) | Moderate severity threshold indicating depressive/anxiety risk | `mental_health_service.py` | VERIFIED |
| Cognitive Disentanglement | Model 2 does not alter Model 1 score or Model 3 probabilities; outputs contextual flag | `app/services/fusion_service.py` | VERIFIED |

### Model 3: Multimodal Speech & Language Assessment Engine
- **Source Package:** `backend/models/model3/neurodetect_model3_process2_package/`
- **Evaluation Report:** `backend/models/model3/neurodetect_model3_process2_package/evaluation/classification_report.json`
- **Metrics Report:** `backend/models/model3/neurodetect_model3_process2_package/evaluation/metrics.json`
- **Confusion Matrix:** `backend/models/model3/neurodetect_model3_process2_package/evaluation/confusion_matrix.json`
- **Model Metadata:** `backend/models/model3/neurodetect_model3_process2_package/model_metadata.json`

| Modality Branch / Metric | Value in White Book | Value in Repository Source | Status |
|---|---|---|---|
| Audio Embedding Accuracy | 61.25% | `"accuracy": 0.6125` | VERIFIED |
| Audio Embedding Macro F1 | 49.90% | `"f1-score": 0.4989759665621735` | VERIFIED |
| Acoustic Feature Accuracy (42 feats) | 68.75% | `"accuracy": 0.6875` | VERIFIED |
| Acoustic Feature Macro F1 | 47.67% | `"f1-score": 0.4766970618034448` | VERIFIED |
| Transcript Accuracy (DistilBERT) | 63.75% | `"accuracy": 0.6375` | VERIFIED |
| Transcript Macro F1 | 55.15% | `"f1-score": 0.5515472182138849` | VERIFIED |
| Multimodal Fusion Accuracy | 70.00% | `"accuracy": 0.70` | VERIFIED |
| Multimodal Fusion Macro F1 | 61.14% | `"f1-score": 0.6114223467164644` | VERIFIED |
| Multimodal Fusion Weighted F1 | 70.97% | `"f1-score": 0.7096755368814193` | VERIFIED |
| Test Partition Size | 80 samples (40 HC, 30 MCI, 10 Dementia) | `support` values in `classification_report.json` | VERIFIED |
| Dataset Source | PROCESS-2 Cookie Theft Task | `README.md` & `model_metadata.json` | VERIFIED |
| Live ASR Pipeline | Faster-Whisper (Systran/faster-whisper) | `backend/app/speech/transcription.py` | VERIFIED |

### Model 4: Deep Transfer Learning MRI Classifier (EfficientNetB0)
- **Source Directory:** `backend/models/model4_mri/neurodetect_mri_model/`
- **Model Binary:** `backend/models/model4_mri/neurodetect_mri_model/mri_model.keras`
- **Evaluation Metrics:** `backend/models/model4_mri/neurodetect_mri_model/evaluation_metrics.json`
- **Classification Report:** `backend/models/model4_mri/neurodetect_mri_model/classification_report.json`
- **Duplicate Audit:** `backend/models/model4_mri/neurodetect_mri_model/duplicate_audit_report.json`
- **Model Config:** `backend/models/model4_mri/neurodetect_mri_model/model_config.json`

| Metric / Parameter | Value in White Book | Value in Repository Source | Status |
|---|---|---|---|
| Architecture | EfficientNetB0 + Custom Dense Head | `"selected_model": "EfficientNetB0"` in `evaluation_metrics.json` | VERIFIED |
| Input Dimensions | 224 x 224 x 3 pixels (2D axial slice) | `"target_size": [224, 224]` in `model_config.json` | VERIFIED |
| Number of Classes | 4 (Non-Dem, Very Mild, Mild, Moderate) | `class_indices.json` | VERIFIED |
| Test Image Count | 1,728 2D slices | `"n_test_images": 1728` | VERIFIED |
| Overall Test Accuracy | 71.01% | `"accuracy": 0.7100694444444444` | VERIFIED |
| Macro Precision | 72.61% | `"precision_macro": 0.7261445024508177` | VERIFIED |
| Macro Recall | 71.62% | `"recall_macro": 0.7162083464833486` | VERIFIED |
| Macro F1 Score | 70.34% | `"f1_macro": 0.703360319880272` | VERIFIED |
| Non-Demented Recall | 88.13% | `"recall": 0.88125` (support: 480) | VERIFIED |
| Moderately Demented F1 | 99.61% | `"f1-score": 0.9961290322580645` (support: 386) | VERIFIED |
| Data Split Caution | Group-level split without subject IDs | `"leakage_status": "GROUP_LEVEL_SPLIT_NO_SUBJECT_IDS"` | VERIFIED |

---

## 3. Figures & Visual Assets Audit Trail

| Figure Name in Report | File Path | Provenance & Description |
|---|---|---|
| Fig 1.1: Boston Cookie Theft Stimulus | `docs/figures/fig_cookie_theft.png` | Standard diagnostic picture stimulus from Goodglass & Kaplan (BDAE) |
| Fig 3.1: System Architecture Diagram | `docs/figures/fig_system_architecture.png` | Generated schematic of Two Independent Pathways and Supabase backend |
| Fig 3.2: Database ER Diagram | `docs/figures/fig_database_er.png` | Relational entity-relationship schema of PostgreSQL database |
| Fig 4.1: Model 1 Top 15 Feature Importances | `docs/figures/fig_model1_feature_importance.png` | Matplotlib plot derived from `feature_importance_xgboost.csv` |
| Fig 5.1: Model 3 Tri-branch Architecture | `docs/figures/fig_model3_multimodal.png` | Schematic showing Wav2Vec2 + Acoustic + DistilBERT late fusion |
| Fig 5.2: Model 4 EfficientNetB0 Pipeline | `docs/figures/fig_model4_efficientnet.png` | Transfer learning architecture with squeeze-and-excitation and head |
| Fig 5.3: Fusion Decision Matrix | `docs/figures/fig_fusion_rules.png` | Rule-based mapping of Model 1 + Model 3 with Model 2 flags |
| Fig 6.1: Render Memory Profile | `docs/figures/fig_render_memory_profile.png` | Empirical RAM footprint across FastAPI, PyTorch, Whisper, and models |
| Fig 6.2: Speech Assessment UI | `docs/figures/fig_speech_assessment_ui.png` | Frontend recording interface screenshot from conversation artifact |
| Fig 6.3: Cognitive Results UI | `docs/figures/fig_results_ui.png` | Final assessment dashboard screenshot showing synthesized conclusion |
| Fig 7.1: Model 3 Branch Comparison Chart | `docs/figures/fig_model3_branch_comparison.png` | Comparative bar chart generated from `classification_report.json` |
| Fig 7.2: Model 3 Multimodal Confusion Matrix | `docs/figures/fig_model3_confusion_matrix.png` | Heatmap generated from `confusion_matrix.json` |
| Fig 7.3: Model 4 MRI Confusion Matrix | `docs/figures/fig_mri_confusion_matrix.png` | Original confusion matrix evaluated on 1,728 test images |
| Fig 7.4: Model 4 MRI ROC Curves | `docs/figures/fig_mri_roc_curves.png` | Original multi-class ROC curves evaluated on test dataset |
| Fig 7.5: Model 4 MRI Training Curves | `docs/figures/fig_mri_training_curves.png` | Original training and validation loss/accuracy across epochs |
| Fig 7.6: Model 4 Grad-CAM Visualization | `docs/figures/fig_mri_gradcam.png` | Saliency map highlighting ventricular enlargement and cortical atrophy |

---

## 4. Software Verification & Test Suite Trail

| Test Suite | Framework | Command | Pass Count | File Locations |
|---|---|---|---|---|
| Backend Complete Suite | pytest 8.3 | `pytest` | **249 passed** (100%) | `backend/tests/` (all test modules) |
| MRI Pathway Isolation Tests | pytest | `pytest tests/test_mri_api.py tests/test_mri_service.py` | 14 passed | `backend/tests/test_mri_*.py` |
| Speech & Audio Tests | pytest | `pytest tests/test_speech_*.py` | 42 passed | `backend/tests/test_speech_*.py` |
| Model 1 & Cognitive Games Tests | pytest | `pytest tests/test_model1_*.py tests/test_games_*.py` | 56 passed | `backend/tests/test_model1_*.py` |
| Rule-Based Fusion Tests | pytest | `pytest tests/test_fusion.py` | 28 passed | `backend/tests/test_fusion.py` |
| Frontend Vitest Suite | Vitest / jsdom | `npm run test` (in `frontend/`) | **11 passed** (100%) | `frontend/src/**/*.test.tsx` |
| Frontend TypeScript Compilation | Vite / tsc | `npm run build` | **0 errors** (Clean build) | `frontend/src/` |

---

## 5. Summary Statement of Academic Integrity
All performance metrics, structural diagrams, database tables, and algorithmic constraints reported in the Semester VII White Book reflect verifiable data extracted directly from the repository code, test suites, and trained model artifacts. Experimental limitations (including synthetic data training for Model 1, group-level dataset splits without patient IDs for Model 4, and ASR transcription mismatches for Model 3) are transparently disclosed and analyzed in accordance with ethical standards in engineering research.
