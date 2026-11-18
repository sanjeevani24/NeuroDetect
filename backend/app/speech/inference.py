"""
Model 3 Inference Manager for NeuroDetect.

Loads the trained PROCESS-2 CTD Model 3 package once through lifecycle management
and executes inference using the official package interface without modifying
feature extraction, weights, or probability calibration.
"""
from __future__ import annotations

import logging
import math
import os
import sys
from pathlib import Path
from typing import Any, Optional

from app.speech.config import MODEL3_DISCLAIMER, MODEL3_PACKAGE_DIR

logger = logging.getLogger("neurodetect.speech.inference")


class Model3InferenceError(Exception):
    """Raised when Model 3 inference fails or returns invalid predictions."""


class Model3Manager:
    _instance: Optional[Model3Manager] = None
    _model = None

    def __init__(self, package_dir: Optional[Path] = None):
        self.package_dir = package_dir or MODEL3_PACKAGE_DIR
        self._ensure_package_exists()

    def _ensure_package_exists(self) -> None:
        if not self.package_dir.exists():
            raise Model3InferenceError(
                f"Model 3 package directory not found at {self.package_dir}. "
                "Ensure neurodetect_model3_process2_package is present."
            )
        inference_py = self.package_dir / "inference" / "predict_model3.py"
        if not inference_py.is_file():
            raise Model3InferenceError(
                f"Model 3 inference script missing at {inference_py}."
            )

    def load_model(self):
        """Loads and caches the NeuroDetectModel3 instance once."""
        if self._model is not None:
            return self._model

        # If encoders are cached locally, prefer offline mode to avoid redundant remote requests
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        if (hf_cache / "models--facebook--wav2vec2-base").exists() and (
            (hf_cache / "models--distilbert-base-uncased").exists()
            or (hf_cache / "models--distilbert--distilbert-base-uncased").exists()
        ):
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("HF_HUB_OFFLINE", "1")

        inference_dir = str(self.package_dir / "inference")
        if inference_dir not in sys.path:
            sys.path.insert(0, inference_dir)

        try:
            from predict_model3 import NeuroDetectModel3  # type: ignore

            logger.info("Initializing NeuroDetectModel3 from %s", self.package_dir)
            self._model = NeuroDetectModel3(str(self.package_dir))
            return self._model
        except ImportError as exc:
            logger.error("Missing dependency for Model 3 inference: %s", exc)
            raise Model3InferenceError(
                f"Missing dependency required for Model 3 inference: {exc}. "
                "Install packages listed in inference/requirements.txt."
            ) from exc
        except Exception as exc:
            logger.error("Failed to load Model 3 package: %s", exc)
            raise Model3InferenceError(f"Failed to initialize Model 3: {exc}") from exc

    def predict(self, audio_path: str, transcript: str) -> dict[str, Any]:
        """
        Executes prediction on the loaded Model 3 instance and validates outputs.
        """
        model = self.load_model()
        try:
            raw_result = model.predict(audio_path=audio_path, transcript=transcript)
        except Exception as exc:
            logger.error("Model 3 inference raised an unhandled exception: %s", type(exc).__name__)
            raise Model3InferenceError(f"Model 3 inference failed: {exc}") from exc

        # Validate prediction structure
        status = raw_result.get("status")
        if status != "ok":
            errors = raw_result.get("errors") or ["Unknown model inference error"]
            logger.error("Model 3 returned error status: %s", errors)
            raise Model3InferenceError(f"Model 3 prediction error: {'; '.join(errors)}")

        predicted_class = raw_result.get("predicted_class")
        if predicted_class not in ("HC", "MCI", "Dementia"):
            raise Model3InferenceError(f"Invalid predicted class '{predicted_class}' returned by Model 3.")

        probabilities = raw_result.get("probabilities")
        if not isinstance(probabilities, dict):
            raise Model3InferenceError("Model 3 did not return a valid probabilities dictionary.")

        # Validate probability distribution: finite, non-negative, sums approx to 1
        total_p = 0.0
        for cls in ("HC", "MCI", "Dementia"):
            if cls not in probabilities:
                raise Model3InferenceError(f"Missing probability for class '{cls}'.")
            p = float(probabilities[cls])
            if not math.isfinite(p) or p < 0.0:
                raise Model3InferenceError(f"Probability for class '{cls}' is non-finite or negative: {p}")
            total_p += p

        if not math.isclose(total_p, 1.0, rel_tol=1e-2, abs_tol=1e-2):
            logger.warning("Probability sum deviates from 1.0: sum = %f", total_p)

        model_version = raw_result.get("model_version")
        if not model_version:
            raise Model3InferenceError("Model version missing in Model 3 output.")

        return {
            "status": "ok",
            "predicted_class": predicted_class,
            "probabilities": {k: float(v) for k, v in probabilities.items()},
            "hc_probability": float(probabilities["HC"]),
            "mci_probability": float(probabilities["MCI"]),
            "dementia_probability": float(probabilities["Dementia"]),
            "branch_probabilities": raw_result.get("branch_probabilities") or {},
            "components_used": raw_result.get("components_used") or [],
            "model_version": str(model_version),
            "disclaimer": raw_result.get("disclaimer") or MODEL3_DISCLAIMER,
        }


_global_manager: Optional[Model3Manager] = None


def get_model3_manager() -> Model3Manager:
    global _global_manager
    if _global_manager is None:
        _global_manager = Model3Manager()
    return _global_manager


def set_model3_manager(manager: Model3Manager) -> None:
    global _global_manager
    _global_manager = manager
