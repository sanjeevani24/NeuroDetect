# NeuroDetect MRI Model (Model 4) - v1.0.0

> **Research prototype for academic use only. Not a medical device and not clinically validated. Outputs must not be used for diagnosis or clinical decision-making. Class labels are inherited from a public dataset and the binary dementia grouping is not a clinical diagnostic definition.**

## Model metadata
| Item | Value |
|---|---|
| Model | NeuroDetect-MRI-EfficientNetB0 (4,054,695 parameters) |
| Task | 4-class stage classification of one 2D MRI image + derived binary grouping |
| Dataset | Kaggle `lukechugh/best-alzheimer-mri-dataset-99-accuracy` (11,519 readable images used) |
| Classes (index) | Non-Demented (0), Very Mildly Demented (1), Mildly Demented (2), Moderately Demented (3) |
| Input | one 2D MRI image -> RGB, resized to 224x224, raw 0-255 floats (normalisation is inside the model) |
| Training | Adam, sparse categorical cross-entropy, seed 42, early stopping + ReduceLROnPlateau |
| Environment | Python 3.13.16, TensorFlow 2.21.0, Keras 3.13.2 |

## IMPORTANT limitations
* **Leakage status: `GROUP_LEVEL_SPLIT_NO_SUBJECT_IDS`.** **The dataset provides no patient/subject identifiers, so patient-level independence between train/validation/test CANNOT be verified.** Splits only keep exact and perceptual near-duplicates together. Reported metrics are **image-level** and may overestimate performance on unseen patients.
* Perceptual hashing does not prove patient independence; flipped/rotated copies are not detected.
* Labels are inherited from a public dataset and not independently verified. The binary grouping (Non-Demented vs. any dementia stage) is not a clinical definition.
* Grad-CAM heatmaps are model-attention explanations only; they do not localise lesions or show causality.
* Test accuracy 0.7101, macro-F1 0.7034 (image-level, n=1728). Minority-class results rest on few images. No "99% accuracy" claim is made.
* This MRI model's output is not ground truth for any other NeuroDetect model.

## Contents
`mri_model.keras`, `class_indices.json`, `model_config.json`, `evaluation_metrics.json`, `training_history.json`, `classification_report.json`,
`confusion_matrix.png`, `training_curves.png`, `roc_curves.png`, `gradcam_examples/`, `inference_example.py`, `duplicate_audit_report.json`,
`duplicate_groups.csv`, `split_manifest.csv`, `test_predictions.csv`, `requirements.txt`, `README.md`.

## Inference (no retraining needed)
```bash
pip install -r requirements.txt
python inference_example.py path/to/mri_slice.jpg
```
```python
import json, tensorflow as tf
from inference_example import predict_mri          # includes the exact training-time preprocessing

model = tf.keras.models.load_model("mri_model.keras", compile=False)
class_indices = json.load(open("class_indices.json"))
result = predict_mri("path/to/mri_slice.jpg", model, class_indices)
print(json.dumps(result, indent=2))
```
Output keys: `predicted_class`, `probability_non_demented`, `probability_very_mild`, `probability_mild`, `probability_moderate`,
`binary_prediction`, `binary_probabilities`, `model_name`, `model_version`, `disclaimer` (plus `predicted_class_index`).
Load the model once at FastAPI start-up and reuse it. Always use the class mapping in `class_indices.json`.
