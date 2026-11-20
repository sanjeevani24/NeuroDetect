from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.mri.inference import MriInferenceError
from app.mri.schemas import MriResultResponse
from app.mri.service import InvalidMriImageError, MriAssessmentNotFoundError, MriService
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.mri_repository import MriRepository

logger = logging.getLogger("neurodetect.mri.router")

router = APIRouter(prefix="/api/assessments", tags=["mri"])


def get_mri_service(client: Client = Depends(get_supabase_client)) -> MriService:
    return MriService(
        assessment_repository=AssessmentRepository(client),
        mri_repository=MriRepository(client),
    )


@router.post(
    "/{assessment_id}/mri/upload",
    response_model=MriResultResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_mri_scan(
    assessment_id: str,
    image: UploadFile = File(...),
    service: MriService = Depends(get_mri_service),
) -> MriResultResponse:
    """
    Receives an individual 2D MRI image slice, validates it,
    executes Model 4 EfficientNetB0 classification, and persists the prediction.
    """
    try:
        UUID(assessment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assessment_id must be a valid UUID.",
        ) from exc

    if not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file was uploaded.",
        )

    try:
        image_bytes = await image.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded image stream.",
        ) from exc

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    filename = image.filename or "mri_scan.png"
    content_type = image.content_type

    try:
        result = await service.process_mri_upload(
            assessment_id=assessment_id,
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type,
        )
        return MriResultResponse(**result)
    except MriAssessmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMriImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except MriInferenceError as exc:
        logger.error("MRI inference failed: %s", exc)
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "MRI inference failed."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc
    except Exception as exc:
        logger.exception("Unexpected error in upload_mri_scan: %s", exc)
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc


@router.get(
    "/{assessment_id}/mri",
    response_model=MriResultResponse,
    status_code=status.HTTP_200_OK,
)
def get_mri_assessment_result(
    assessment_id: str,
    service: MriService = Depends(get_mri_service),
) -> MriResultResponse:
    """
    Retrieves the persisted Model 4 MRI assessment result.
    """
    try:
        UUID(assessment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assessment_id must be a valid UUID.",
        ) from exc

    try:
        result = service.get_mri_result(assessment_id)
    except MriAssessmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MRI assessment result not found.",
        )
    return MriResultResponse(**result)
