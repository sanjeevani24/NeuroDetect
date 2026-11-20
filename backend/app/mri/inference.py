from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from app.mri.config import (
    CLASS_INDICES_FILE_NAME,
    DISCLAIMER,
    IMG_SIZE,
    MODEL4_PACKAGE_DIR,
    MODEL_FILE_NAME,
    MODEL_NAME,
    MODEL_VERSION,
    NON_DEMENTED_LABEL,
    PROBABILITY_KEYS,
)

logger = logging.getLogger("neurodetect.mri.inference")

_RESAMPLE = getattr(Image, "Resampling", Image).BILINEAR


class MriInferenceError(Exception):
    """Raised when MRI Model 4 inference or preprocessing fails."""


class MriModelManager:
    _instance: Optional[MriModelManager] = None
    _model = None
    _class_indices: Optional[dict[str, int]] = None

    def __init__(self, package_dir: Optional[Path] = None):
        self.package_dir = package_dir or MODEL4_PACKAGE_DIR
        self._ensure_package_exists()

    def _ensure_package_exists(self) -> None:
        if not self.package_dir.exists():
            raise MriInferenceError(
                f"Model 4 package directory not found at {self.package_dir}. "
                "Ensure neurodetect_mri_model is present."
            )
        model_file = self.package_dir / MODEL_FILE_NAME
        if not model_file.is_file():
            raise MriInferenceError(f"Model 4 artifact missing at {model_file}.")

    def load_model(self):
        """Loads and caches the Keras EfficientNetB0 model and class mapping once."""
        if self._model is not None and self._class_indices is not None:
            return self._model, self._class_indices

        try:
            import tensorflow as tf
        except ImportError as exc:
            logger.error("TensorFlow is not installed in the environment: %s", exc)
            raise MriInferenceError(
                "Missing dependency required for Model 4 inference: tensorflow. "
                "Ensure tensorflow>=2.21 is installed."
            ) from exc

        model_file = self.package_dir / MODEL_FILE_NAME
        class_file = self.package_dir / CLASS_INDICES_FILE_NAME

        try:
            logger.info("Loading MRI Model 4 from %s", model_file)
            self._model = tf.keras.models.load_model(str(model_file), compile=False)
            with open(class_file, encoding="utf-8") as f:
                self._class_indices = json.load(f)
            logger.info("MRI Model 4 loaded successfully. Input shape: %s", self._model.input_shape)
            return self._model, self._class_indices
        except Exception as exc:
            logger.error("Failed to load MRI Model 4 package: %s", exc)
            raise MriInferenceError(f"Failed to initialize Model 4: {exc}") from exc

    @staticmethod
    def preprocess_image(image_input: str | Path | bytes | io.BytesIO, target_size: int = IMG_SIZE) -> np.ndarray:
        """
        Open one 2D MRI image, convert to 3-channel RGB, and resize to (target_size, target_size).
        Returns a float32 batch array of shape (1, target_size, target_size, 3) with raw 0-255 values.
        Intensity normalisation is performed INSIDE the saved Keras model.
        """
        try:
            if isinstance(image_input, (str, Path)):
                im = Image.open(image_input)
            elif isinstance(image_input, bytes):
                im = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, io.BytesIO):
                im = Image.open(image_input)
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")

            with im:
                im_rgb = im.convert("RGB")
                im_resized = im_rgb.resize((target_size, target_size), _RESAMPLE)
                arr = np.asarray(im_resized, dtype=np.uint8)

            # Model expects batch dimension and float32 values [0, 255]
            batch = np.expand_dims(arr.astype("float32"), axis=0)
            return batch
        except Exception as exc:
            logger.error("MRI image preprocessing failed: %s", exc)
            raise MriInferenceError(f"Unable to process MRI image file: {exc}") from exc

    def predict(self, image_input: str | Path | bytes | io.BytesIO) -> dict[str, Any]:
        """
        Executes prediction on the preprocessed 2D MRI image and returns structured probabilities.
        """
        model, class_indices = self.load_model()
        batch = self.preprocess_image(image_input)

        try:
            probs = np.asarray(model.predict(batch, verbose=0))[0].astype("float64")
        except Exception as exc:
            logger.error("MRI Model 4 inference execution failed: %s", exc)
            raise MriInferenceError(f"Model 4 inference execution error: {exc}") from exc

        idx_to_class = {int(v): k for k, v in class_indices.items()}
        if len(probs) != len(idx_to_class):
            raise MriInferenceError("Model output dimension does not match class_indices.json mapping.")

        by_class = {idx_to_class[i]: float(probs[i]) for i in range(len(probs))}
        pred_idx = int(np.argmax(probs))
        predicted_class = idx_to_class[pred_idx]

        p_no = by_class[NON_DEMENTED_LABEL]
        p_dem = float(sum(v for k, v in by_class.items() if k != NON_DEMENTED_LABEL))

        result: dict[str, Any] = {
            "predicted_class": predicted_class,
            "predicted_class_index": pred_idx,
            "class_probabilities": by_class,
            "binary_prediction": "Dementia" if p_dem >= 0.5 else "No Dementia",
            "binary_probabilities": {
                "no_dementia": p_no,
                "dementia": p_dem,
            },
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "disclaimer": DISCLAIMER,
        }

        for cls_name, key in PROBABILITY_KEYS.items():
            result[key] = by_class.get(cls_name, 0.0)

        return result


_global_mri_manager: Optional[MriModelManager] = None


def get_mri_manager() -> MriModelManager:
    global _global_mri_manager
    if _global_mri_manager is None:
        _global_mri_manager = MriModelManager()
    return _global_mri_manager


def set_mri_manager(manager: MriModelManager) -> None:
    global _global_mri_manager
    _global_mri_manager = manager
