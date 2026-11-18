from __future__ import annotations

from uuid import UUID

from app.ml.model1.config import MODEL_NAME, MODEL_VERSION
from app.ml.model1.exceptions import (
    Model1FeatureValidationError,
    Model1IncompleteAssessmentError,
    Model1PredictionError,
)
from app.ml.model1.feature_aggregator import Model1FeatureAggregator
from app.ml.model1.model import predict_cognitive_performance
from app.ml.model1.schemas import Model1FeatureVectorResponse, Model1PredictionResponse


class InvalidModel1AssessmentIdError(ValueError):
    """Raised when assessment_id is not a valid UUID."""


class Model1AssessmentNotFoundError(ValueError):
    """Raised when the referenced assessment does not exist."""


class Model1Service:
    def __init__(self, *, assessment_repository, model1_repository, feature_aggregator: Model1FeatureAggregator):
        self._assessment_repository = assessment_repository
        self._model1_repository = model1_repository
        self._feature_aggregator = feature_aggregator

    def predict(self, assessment_id: str) -> Model1PredictionResponse:
        self._validate_assessment_id(assessment_id)
        if not self._assessment_repository.assessment_exists(assessment_id):
            raise Model1AssessmentNotFoundError(f"assessment_id '{assessment_id}' does not exist.")

        existing = self._model1_repository.get_by_assessment(assessment_id)
        if existing is not None:
            return Model1PredictionResponse(
                assessment_id=assessment_id,
                model=existing["model_name"],
                model_version=existing["model_version"],
                cognitive_performance_score=float(existing["cognitive_performance_score"]),
                status="existing",
            )

        feature_vector = self._feature_aggregator.build_feature_vector(assessment_id)
        prediction = predict_cognitive_performance(feature_vector)
        row = self._model1_repository.insert_result(
            assessment_id=assessment_id,
            cognitive_performance_score=prediction,
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            feature_vector=feature_vector,
        )
        return Model1PredictionResponse(
            assessment_id=assessment_id,
            model=row["model_name"],
            model_version=row["model_version"],
            cognitive_performance_score=float(row["cognitive_performance_score"]),
            status="success",
        )

    def get_result(self, assessment_id: str) -> Model1FeatureVectorResponse | None:
        self._validate_assessment_id(assessment_id)
        row = self._model1_repository.get_by_assessment(assessment_id)
        if row is None:
            return None
        return Model1FeatureVectorResponse(
            assessment_id=assessment_id,
            model=row["model_name"],
            model_version=row["model_version"],
            cognitive_performance_score=float(row["cognitive_performance_score"]),
            feature_vector={key: float(value) for key, value in row["feature_vector"].items()},
        )

    @staticmethod
    def _validate_assessment_id(assessment_id: str) -> None:
        try:
            UUID(assessment_id)
        except ValueError as exc:
            raise InvalidModel1AssessmentIdError("assessment_id must be a valid UUID.") from exc
