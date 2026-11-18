import math

import pytest

from app.ml.model1.exceptions import Model1IncompleteAssessmentError
from app.ml.model1.feature_aggregator import Model1FeatureAggregator
from app.ml.model1.service import (
    InvalidModel1AssessmentIdError,
    Model1AssessmentNotFoundError,
    Model1Service,
)
from tests.model1.test_feature_aggregator import ASSESSMENT_ID, build_aggregator


class FakeAssessmentRepository:
    def __init__(self, exists: bool = True):
        self._exists = exists

    def assessment_exists(self, assessment_id: str) -> bool:
        return self._exists


class FakeModel1Repository:
    def __init__(self, existing=None):
        self._existing = existing
        self.inserted = None

    def get_by_assessment(self, assessment_id: str):
        return self._existing

    def insert_result(self, **payload):
        self.inserted = payload
        self._existing = payload
        return payload


def build_service(
    *,
    assessment_exists: bool = True,
    existing_result=None,
    aggregator: Model1FeatureAggregator | None = None,
):
    return Model1Service(
        assessment_repository=FakeAssessmentRepository(assessment_exists),
        model1_repository=FakeModel1Repository(existing_result),
        feature_aggregator=aggregator or build_aggregator(),
    )


def test_invalid_assessment_id_rejected():
    service = build_service()
    with pytest.raises(InvalidModel1AssessmentIdError):
        service.predict("not-a-uuid")


def test_missing_assessment_rejected():
    service = build_service(assessment_exists=False)
    with pytest.raises(Model1AssessmentNotFoundError):
        service.predict(ASSESSMENT_ID)


def test_duplicate_result_returns_existing():
    service = build_service(
        existing_result={
            "assessment_id": ASSESSMENT_ID,
            "model_name": "NeuroDetect Model 1 - Cognitive Performance Regressor",
            "model_version": "1.0.0",
            "cognitive_performance_score": 78.5,
            "feature_vector": {},
        }
    )
    result = service.predict(ASSESSMENT_ID)
    assert result.status == "existing"
    assert result.cognitive_performance_score == 78.5


def test_prediction_succeeds_and_persists():
    service = build_service()
    result = service.predict(ASSESSMENT_ID)
    assert result.status == "success"
    assert math.isfinite(result.cognitive_performance_score)


def test_incomplete_assessment_bubbles_up():
    broken_aggregator = build_aggregator()
    broken_aggregator = Model1FeatureAggregator(
        mmse_repository=broken_aggregator._mmse_repository,
        memory_repository=broken_aggregator._memory_repository,
        nback_repository=broken_aggregator._nback_repository,
        boston_repository=broken_aggregator._boston_repository,
        trail_repository=type("MissingRepo", (), {"get_by_assessment": lambda self, assessment_id: None})(),
    )
    service = build_service(aggregator=broken_aggregator)
    with pytest.raises(Model1IncompleteAssessmentError):
        service.predict(ASSESSMENT_ID)
