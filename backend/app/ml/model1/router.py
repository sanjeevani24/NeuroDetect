from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.ml.model1.exceptions import (
    Model1FeatureValidationError,
    Model1IncompleteAssessmentError,
    Model1PredictionError,
    Model1SchemaNotReadyError,
)
from app.ml.model1.feature_aggregator import Model1FeatureAggregator
from app.ml.model1.schemas import Model1FeatureVectorResponse, Model1PredictionResponse
from app.ml.model1.service import (
    InvalidModel1AssessmentIdError,
    Model1AssessmentNotFoundError,
    Model1Service,
)
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.boston_naming_repository import BostonNamingRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.mmse_repository import MMSERepository
from app.repositories.model1_repository import Model1Repository
from app.repositories.nback_repository import NBackRepository
from app.repositories.trail_making_repository import TrailMakingRepository

router = APIRouter(prefix="/api/assessments", tags=["model1"])


def get_model1_service(client: Client = Depends(get_supabase_client)) -> Model1Service:
    aggregator = Model1FeatureAggregator(
        mmse_repository=MMSERepository(client),
        memory_repository=MemoryRepository(client),
        nback_repository=NBackRepository(client),
        boston_repository=BostonNamingRepository(client),
        trail_repository=TrailMakingRepository(client),
    )
    return Model1Service(
        assessment_repository=AssessmentRepository(client),
        model1_repository=Model1Repository(client),
        feature_aggregator=aggregator,
    )


@router.post("/{assessment_id}/model1/predict", response_model=Model1PredictionResponse)
def predict_model1(
    assessment_id: str,
    service: Model1Service = Depends(get_model1_service),
) -> Model1PredictionResponse:
    try:
        return service.predict(assessment_id)
    except InvalidModel1AssessmentIdError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Model1AssessmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Model1IncompleteAssessmentError as exc:
        raise HTTPException(
            status_code=409,
            detail={"detail": "Cognitive assessment incomplete", "missing_games": exc.missing_games},
        ) from exc
    except Model1SchemaNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (Model1FeatureValidationError, Model1PredictionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None


@router.get("/{assessment_id}/model1", response_model=Model1FeatureVectorResponse)
def get_model1_result(
    assessment_id: str,
    service: Model1Service = Depends(get_model1_service),
) -> Model1FeatureVectorResponse:
    try:
        result = service.get_result(assessment_id)
    except InvalidModel1AssessmentIdError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Model1SchemaNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Model 1 result not found.")
    return result
