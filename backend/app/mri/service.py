from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from PIL import Image, UnidentifiedImageError

from app.mri.config import (
    MAX_IMAGE_SIZE_BYTES,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_IMAGE_MIME_TYPES,
)
from app.mri.inference import MriInferenceError, MriModelManager, get_mri_manager
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.mri_repository import MriRepository

logger = logging.getLogger("neurodetect.mri.service")


class MriAssessmentNotFoundError(Exception):
    """Raised when assessment does not exist."""


class InvalidMriImageError(Exception):
    """Raised when uploaded file is not a valid or supported 2D MRI image."""


class MriService:
    def __init__(
        self,
        assessment_repository: AssessmentRepository,
        mri_repository: MriRepository,
        model_manager: Optional[MriModelManager] = None,
    ):
        self._assessment_repo = assessment_repository
        self._mri_repo = mri_repository
        self._model_manager = model_manager or get_mri_manager()

    def get_mri_result(self, assessment_id: str) -> Optional[dict[str, Any]]:
        self._validate_uuid(assessment_id)
        if not self._assessment_repo.assessment_exists(assessment_id):
            raise MriAssessmentNotFoundError("Assessment not found.")
        raw = self._mri_repo.get_by_assessment(assessment_id)
        if not raw:
            return None

        # Reconstitute nested class_probabilities and binary_probabilities
        class_probabilities = {
            "Non-Demented": raw.get("probability_non_demented", 0.0),
            "Very Mildly Demented": raw.get("probability_very_mild", 0.0),
            "Mildly Demented": raw.get("probability_mild", 0.0),
            "Moderately Demented": raw.get("probability_moderate", 0.0),
        }
        binary_probabilities = {
            "no_dementia": raw.get("binary_probability_no_dementia", 0.0),
            "dementia": raw.get("binary_probability_dementia", 0.0),
        }

        return {
            **raw,
            "status": "completed",
            "class_probabilities": class_probabilities,
            "binary_probabilities": binary_probabilities,
        }

    async def process_mri_upload(
        self,
        *,
        assessment_id: str,
        image_bytes: bytes,
        filename: str = "mri_scan.png",
        content_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Validates the 2D MRI image, runs Model 4 EfficientNetB0 inference,
        and persists the resulting prediction into the database.
        """
        self._validate_uuid(assessment_id)

        # 1. Verify assessment exists
        if not self._assessment_repo.assessment_exists(assessment_id):
            logger.warning("MRI upload rejected: assessment_id %s not found", assessment_id)
            raise MriAssessmentNotFoundError("Assessment not found.")

        # 2. Validate image payload
        image_format, image_size = self._validate_image(image_bytes, filename, content_type)

        # 3. Model 4 inference
        try:
            prediction = self._model_manager.predict(image_bytes)
        except MriInferenceError as exc:
            logger.error("Model 4 inference failed on image %s: %s", filename, exc)
            raise

        # 4. Persist to repository
        saved_row = self._mri_repo.upsert_mri_result(
            assessment_id=assessment_id,
            image_filename=filename,
            image_format=image_format,
            image_size_bytes=image_size,
            processing_status="completed",
            model_name=prediction["model_name"],
            model_version=prediction["model_version"],
            predicted_class=prediction["predicted_class"],
            predicted_class_index=prediction["predicted_class_index"],
            probability_non_demented=prediction["probability_non_demented"],
            probability_very_mild=prediction["probability_very_mild"],
            probability_mild=prediction["probability_mild"],
            probability_moderate=prediction["probability_moderate"],
            binary_prediction=prediction["binary_prediction"],
            binary_probability_dementia=prediction["binary_probabilities"]["dementia"],
            binary_probability_no_dementia=prediction["binary_probabilities"]["no_dementia"],
            disclaimer=prediction["disclaimer"],
        )

        return {
            "assessment_id": assessment_id,
            "status": "completed",
            "processing_status": "completed",
            "image_filename": filename,
            "image_format": image_format,
            "image_size_bytes": image_size,
            "predicted_class": prediction["predicted_class"],
            "predicted_class_index": prediction["predicted_class_index"],
            "probability_non_demented": prediction["probability_non_demented"],
            "probability_very_mild": prediction["probability_very_mild"],
            "probability_mild": prediction["probability_mild"],
            "probability_moderate": prediction["probability_moderate"],
            "class_probabilities": prediction["class_probabilities"],
            "binary_prediction": prediction["binary_prediction"],
            "binary_probabilities": prediction["binary_probabilities"],
            "model_name": prediction["model_name"],
            "model_version": prediction["model_version"],
            "disclaimer": prediction["disclaimer"],
            "created_at": saved_row.get("created_at") if isinstance(saved_row, dict) else None,
            "updated_at": saved_row.get("updated_at") if isinstance(saved_row, dict) else None,
        }

    @staticmethod
    def _validate_uuid(assessment_id: str) -> None:
        try:
            UUID(assessment_id)
        except ValueError as exc:
            raise ValueError(f"assessment_id '{assessment_id}' is not a valid UUID.") from exc

    @staticmethod
    def _validate_image(
        image_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> tuple[str, int]:
        if not image_bytes or len(image_bytes) == 0:
            raise InvalidMriImageError("Uploaded image file is empty.")

        size = len(image_bytes)
        if size > MAX_IMAGE_SIZE_BYTES:
            max_mb = MAX_IMAGE_SIZE_BYTES // (1024 * 1024)
            raise InvalidMriImageError(f"Image exceeds maximum allowed size of {max_mb} MB.")

        ext = Path(filename).suffix.lower()
        if ext and ext not in SUPPORTED_IMAGE_EXTENSIONS:
            raise InvalidMriImageError(
                f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}."
            )

        if content_type and content_type.lower() not in SUPPORTED_IMAGE_MIME_TYPES:
            # Allow fallback if file extension is valid
            if not ext or ext not in SUPPORTED_IMAGE_EXTENSIONS:
                raise InvalidMriImageError(
                    f"Unsupported image MIME type '{content_type}'. Must be JPEG, PNG, WebP, or BMP."
                )

        try:
            with Image.open(io.BytesIO(image_bytes)) as im:
                im.verify()
                format_name = (im.format or ext.lstrip(".") or "png").lower()
                width, height = im.size
                if width < 16 or height < 16:
                    raise InvalidMriImageError("Image dimensions are too small to be a valid 2D MRI slice.")
        except UnidentifiedImageError as exc:
            raise InvalidMriImageError("Uploaded file could not be identified as an image.") from exc
        except Exception as exc:
            if isinstance(exc, InvalidMriImageError):
                raise
            raise InvalidMriImageError(f"Corrupt or invalid image file: {exc}") from exc

        return format_name, size
