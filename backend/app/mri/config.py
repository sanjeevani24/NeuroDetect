from __future__ import annotations

import os
from pathlib import Path

# Ensure Keras config directory works inside sandboxed and containerized environments
os.environ.setdefault("KERAS_HOME", "/tmp/.keras")

# Paths
DEFAULT_PACKAGE_DIR = (
    Path(__file__).resolve().parents[2] / "models" / "model4_mri" / "neurodetect_mri_model"
)
MODEL4_PACKAGE_DIR = Path(
    os.getenv("MODEL4_PACKAGE_DIR", str(DEFAULT_PACKAGE_DIR))
)

MODEL_FILE_NAME = "mri_model.keras"
CLASS_INDICES_FILE_NAME = "class_indices.json"
MODEL_CONFIG_FILE_NAME = "model_config.json"

# Image constraints
IMG_SIZE = 224
MAX_IMAGE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

SUPPORTED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
}

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}

# Model metadata
MODEL_NAME = "NeuroDetect-MRI-EfficientNetB0"
MODEL_VERSION = "1.0.0"

CLASS_NAMES = [
    "Non-Demented",
    "Very Mildly Demented",
    "Mildly Demented",
    "Moderately Demented",
]

NON_DEMENTED_LABEL = "Non-Demented"
BINARY_THRESHOLD = 0.5

PROBABILITY_KEYS = {
    "Non-Demented": "probability_non_demented",
    "Very Mildly Demented": "probability_very_mild",
    "Mildly Demented": "probability_mild",
    "Moderately Demented": "probability_moderate",
}

DISCLAIMER = (
    "Research prototype for academic use only. Not a medical device and not clinically validated. "
    "Outputs must not be used for diagnosis or clinical decision-making. Class labels are inherited "
    "from a public dataset and the binary dementia grouping is not a clinical diagnostic definition. "
    "This model processes individual 2D MRI slices and does not analyze full 3D volumetric MRI scans."
)
